from enum import Enum
from typing import Dict, Any, Optional
import json
import configs
from llm import LLMConnector
from enviroment_tools import execute_tool, check_all_nodes_status
from jsonschema import validate, ValidationError
from world import WORLD_STATE

class State(Enum):
    INIT = 0
    FAILURE_DETECTION = 1
    IMPACT_ANALYSIS = 2
    REPAIR_PLANNING = 3
    REPAIR_VALIDATOR = 4
    REPAIR_EXECUTOR = 5
    FINAL = 6

class InfrastructureRepairAgent:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-Coder-32B-Instruct"):
        self.model_id = model_id
        self.state = State.INIT
        self.history = []
        
    def get_context(self):
        return self.history

    def update_history(self, role, content):
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        self.history.append({"role": role, "content": content})

    def run(self, maxsteps=20):
        steps = 0
        self.traces = []

        while self.state != State.FINAL and steps < maxsteps:
            steps += 1
            # Check if all nodes are repaired
            status = check_all_nodes_status()
            if status["all_repaired"]:
                self.state = State.FINAL
                break
            
            if self.state == State.INIT:
                self.state = State.FAILURE_DETECTION
                continue

            elif self.state == State.FAILURE_DETECTION:
                state_config = configs.STATES_CONFIGS[State.FAILURE_DETECTION.name]
                prompt = state_config["prompt"]
                
                # Add user prompt to global history
                self.update_history("user", prompt)
                
                response_data = self._run_llm(
                    State.FAILURE_DETECTION.name,
                    state_config,
                    prompt
                )

                self.update_history("assistant", json.dumps(response_data))
                
                # Transition to next state
                next_state = response_data.get('transition', State.IMPACT_ANALYSIS.name)
                if next_state == State.IMPACT_ANALYSIS.name:
                    self.state = State.IMPACT_ANALYSIS
                continue
            
            elif self.state == State.IMPACT_ANALYSIS:
                state_config = configs.STATES_CONFIGS[State.IMPACT_ANALYSIS.name]
                prompt = state_config["prompt"]
                
                # Add user prompt to global history
                self.update_history("user", prompt)
                
                response_data = self._run_llm(
                    State.IMPACT_ANALYSIS.name,
                    state_config,
                    prompt
                )
                
                self.update_history("assistant", json.dumps(response_data))
                
                # Check if no failed nodes detected (all in repair or repaired)
                if not response_data.get('priority_list') or len(response_data.get('priority_list', [])) == 0:
                    # No failures detected - check status
                    status = check_all_nodes_status()
                    if status["nodes_in_repair"]:
                        # Nodes are being repaired - advance simulation time
                        from enviroment_tools import step_simulation_time
                        step_simulation_time()
                        print(f"\n=== No failures detected. Advancing simulation time to {WORLD_STATE['simulation_time']}. Nodes in repair: {status['nodes_in_repair']} ===")
                        # Stay in IMPACT_ANALYSIS to check again
                        continue
                    else:
                        self.state = State.FINAL
                        continue
                
                # Transition
                next_state = response_data.get('transition', State.REPAIR_PLANNING.name)
                if next_state == State.REPAIR_PLANNING.name:
                    self.state = State.REPAIR_PLANNING
                continue
            
            elif self.state == State.REPAIR_PLANNING:
                state_config = configs.STATES_CONFIGS[State.REPAIR_PLANNING.name]
                prompt = state_config["prompt"]
                
                self.update_history("user", prompt)
                
                response_data = self._run_llm(
                    State.REPAIR_PLANNING.name,
                    state_config,
                    prompt
                )
                
                self.update_history("assistant", json.dumps(response_data))
                
                # Transition
                next_state = response_data.get('transition', State.REPAIR_VALIDATOR.name)
                if next_state == State.REPAIR_VALIDATOR.name:
                    self.state = State.REPAIR_VALIDATOR
                    self.repair_plan_data = response_data
                continue

            elif self.state == State.REPAIR_VALIDATOR:
                if not hasattr(self, 'repair_plan_data') or not self.repair_plan_data:
                    self.state = State.FINAL
                    continue
                
                validation_result = self._validate_repair_plan(self.repair_plan_data)
                
                if validation_result['valid']:
                    self.state = State.REPAIR_EXECUTOR
                else:
                    # Validation failed - return to IMPACT_ANALYSIS with error feedback
                    self.update_history("user", f"Validation failed: {json.dumps(validation_result)}. Please revise the repair plan based on these errors.")
                    self.state = State.IMPACT_ANALYSIS
                continue

            elif self.state == State.REPAIR_EXECUTOR:
                state_config = configs.STATES_CONFIGS[State.REPAIR_EXECUTOR.name]
                prompt = state_config["prompt"]
                
                # Add user prompt to global history
                self.update_history("user", prompt)
                
                response_data = self._run_llm(
                    State.REPAIR_EXECUTOR.name,
                    state_config,
                    prompt
                )
                
                self.update_history("assistant", json.dumps(response_data))
                
                # After executing repairs, return to FAILURE_DETECTION to check status
                self.state = State.FAILURE_DETECTION
                continue

            elif self.state == State.FINAL:
                break
        
        return {
            "history": self.history,
            "traces": self.traces
        }
    
    # Main Run LLM Loop With Retries and Tool Handling
    def _run_llm(self, state_name: str, state_config: Dict[str, Any], prompt: str, max_retries: int = 2) -> Dict[str, Any]:
        # Create a local copy of history for tool interactions
        local_history = self.history.copy()
        
        llm = LLMConnector(
            model_id=self.model_id,
            system_prompt=state_config["system_prompt"],
            tools=state_config.get("tools"),
            messages=local_history,
            sliding_window=state_config.get("sliding_window"),
            response_schema=state_config.get("schema")
        )
        
        for attempt in range(max_retries):
            try:
                trace_data = {'prompt': prompt, 'raw_responses': [], 'actions': [], 'observations': []}
                response, tool_calls = self._execute_with_tools(llm, prompt, state_name, local_history, state_config, trace_data=trace_data)
                self._trace(state_name, trace_data, response)
                return response
                    
            except json.JSONDecodeError as je:
                if attempt < max_retries - 1:
                    error_feedback = f"JSON parse error: {str(je)}. Please provide valid JSON only."
                    self._update_local_history(local_history, "user", error_feedback)
                    prompt = "Respond with ONLY a valid JSON object. No text before or after. No markdown. Just pure JSON starting with {{ and ending with }}."
                else:
                    raise
            except ValidationError as ve:
                if attempt < max_retries - 1:
                    error_msg = f"Schema validation failed: {ve.message}"
                    error_feedback = f"Validation error: {error_msg}. Please fix the JSON response to match the schema exactly."
                    self._update_local_history(local_history, "user", error_feedback)
                    prompt = "Please provide the response again, ensuring it matches the required JSON schema."
                else:
                    raise
        
        raise Exception(f"Failed to get valid response after {max_retries} attempts")

    def _execute_with_tools(self, llm: LLMConnector, prompt: str, state_name: str, local_history: list, state_config: Dict[str, Any], all_tool_calls=None, trace_data=None):
        """Recursively execute LLM with tools until no more tool calls are needed."""
        if all_tool_calls is None:
            all_tool_calls = []
        if trace_data is None:
            trace_data = {'prompt': prompt, 'raw_responses': [], 'actions': [], 'observations': []}
        
        # Update the LLM's messages with current local history
        llm.messages = local_history
        
        response = llm.run(prompt)
        raw_response = LLMConnector.get_text_response(response)
        trace_data['raw_responses'].append(raw_response)

        schema = state_config.get("schema")
        if schema:
            try:
                parsed_response = LLMConnector.parse_json_response(raw_response, schema)
                return parsed_response, all_tool_calls
            except (json.JSONDecodeError, ValidationError):
                pass
        
        # Check for tool calls
        tool_calls = LLMConnector.get_tool_calls(response)
        
        if tool_calls:
            all_tool_calls.extend(tool_calls)
            tool_results = []
            
            for tool_call in tool_calls:
                func_name = tool_call['function']['name']
                func_args = json.loads(tool_call['function']['arguments']) if isinstance(tool_call['function']['arguments'], str) else tool_call['function']['arguments']
                result = execute_tool(func_name, func_args)
                
                # Track action and observation
                trace_data['actions'].append(f"CALL_TOOL: {func_name}({json.dumps(func_args)})")
                trace_data['observations'].append({func_name: result})
                
                tool_result_text = f"Tool '{func_name}' result: {json.dumps(result)}"
                tool_results.append(tool_result_text)
            
            for tool_result in tool_results:
                self._update_local_history(local_history, "user", tool_result)
            
            # After tool execution, ask for structured response with schema
            if schema:
                final_prompt = f"Based on the tool results above, provide your complete analysis as a valid JSON object matching this schema:\n\n{json.dumps(schema, indent=2)}\n\nRespond with ONLY the JSON object. No explanatory text, no markdown code blocks, no text before or after the JSON. Just the pure JSON object starting with {{ and ending with }}."
            else:
                final_prompt = "Based on the tool results above, provide your final response."
            
            return self._execute_with_tools(llm, final_prompt, state_name, local_history, state_config, all_tool_calls, trace_data)
        else:
            # No tool calls - this is the final response, parse it
            parsed_response = LLMConnector.parse_json_response(raw_response, schema)
            return parsed_response, all_tool_calls


    def _update_local_history(self, local_history: list, role: str, content: str):
        """Update local history with proper formatting."""
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        local_history.append({"role": role, "content": content})

    def _validate_repair_plan(self, plan: dict) -> dict:
        errors = []
        assignments = plan.get('assignments', [])
        
        if not assignments:
            return {"valid": False, "errors": ["No assignments in plan"]}
        
        available_crews = {
            crew_id: crew['availability'] 
            for crew_id, crew in WORLD_STATE['crews'].items()
        }
        
        for assignment in assignments:
            crew_id = assignment.get('crew_id')
            node_id = assignment.get('node_id')
            
            if crew_id not in WORLD_STATE['crews']:
                errors.append(f"Crew '{crew_id}' does not exist")
                continue
            
            if node_id not in WORLD_STATE['nodes']:
                errors.append(f"Node '{node_id}' does not exist")
                continue
            
            crew = WORLD_STATE['crews'][crew_id]
            node = WORLD_STATE['nodes'][node_id]
            
            if not available_crews.get(crew_id, False):
                errors.append(f"Crew '{crew_id}' is not available")
                continue
            
            if node['status'] != 'failed':
                errors.append(f"Node '{node_id}' is not in failed state (status: {node['status']})")
                continue
            
            if node['type'] not in crew['skills']:
                errors.append(f"Crew '{crew_id}' lacks skill for node type '{node['type']}'")
                continue
            
            available_crews[crew_id] = False
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _trace(self, state: str, trace_data: Dict[str, Any], response: Dict[str, Any]):
        """Print and store trace for LLM execution."""
        print("\n--- TRACE EVENT ---")
        print(f"[STATE] {state}")
        print(f"[PROMPT] {trace_data['prompt']}...") 
        print(f"[RAW LLM] {trace_data['raw_responses'][0]}...") 
        if trace_data['actions']:
            print(f"[ACTION] {'; '.join(trace_data['actions'])}")
        if trace_data['observations']:
            observations_str = json.dumps(trace_data['observations'], indent=2)
            print(f"[OBSERVATION] {observations_str}")
        print("--\n")
        
        self.traces.append({
            "state": state,
            "prompt": trace_data['prompt'],
            "raw_responses": trace_data['raw_responses'],
            "actions": trace_data['actions'],
            "observations": trace_data['observations'],
            "final_response": response
        })

