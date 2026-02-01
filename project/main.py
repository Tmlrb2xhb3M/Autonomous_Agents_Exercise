from dotenv import load_dotenv
load_dotenv()

import json
from llm import LLMConnector
from prompts import observer_system_prompt, SCHEMA
from enviroment_tools import OBSERVER_TOOL_REGISTRY

def execute_tool(tool_name: str, tool_args: dict):
    """Execute a tool by name with given arguments."""
    tool = OBSERVER_TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {"error": f"Tool '{tool_name}' not found"}
    
    try:
        result = tool(**tool_args)
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}


def run_observer_agent_with_tools(prompt: str, max_steps: int = 10):
    """
    Run observer agent with mock tool calling loop.
    Simulates agentic behavior by executing tools and feeding results back to LLM.
    """
    print("\n" + "="*70)
    print("OBSERVER AGENT - TOOL CALLING LOOP")
    print("="*70 + "\n")
    
    # Initialize LLM caller
    llm_caller = LLMConnector(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        system_prompt=observer_system_prompt,
        tools=list(OBSERVER_TOOL_REGISTRY.values()),
        messages=[],
        sliding_window=None,
        max_steps=max_steps,
        response_schema=SCHEMA
    )
    
    # Make initial call
    print(f"[Step 0] Initial prompt: {prompt}\n")
    response = llm_caller.run(prompt)
    
    # Tool calling loop
    for step in range(1, max_steps + 1):
        print(f"\n{'─'*70}")
        print(f"[Step {step}]")
        print(f"{'─'*70}\n")
        
        # Extract tool calls
        tool_calls = LLMConnector.get_tool_calls(response)
        text_response = LLMConnector.get_text_response(response)
        
        print(f"Response content: {text_response}")
        
        if not tool_calls:
            print("\n✓ No tool calls detected. Agent has completed its task.")
            print("\n" + "="*70)
            print("FINAL RESPONSE")
            print("="*70 + "\n")
            
            final_output = LLMConnector.parse_json_response(text_response, SCHEMA)
            
            if final_output:
                print(final_output)
                print("\n✓ Response validates against schema")
            else:
                print("✗ Failed to parse or validate JSON response")
                print(text_response)
            
            return response
        
        print(f"\n✓ Found {len(tool_calls)} tool call(s)")
        
        # Execute each tool call
        tool_results = []
        for idx, tool_call in enumerate(tool_calls, 1):
            function_name = tool_call['function']['name']
            function_args = json.loads(tool_call['function']['arguments'])
            
            print(f"\n  [{idx}] Calling tool: {function_name}")
            print(f"      Arguments: {function_args}")
            
            # Execute the tool
            result = execute_tool(function_name, function_args)
            
            print(f"      Result: {result}")
            
            tool_results.append({
                'role': 'user',
                'content': f"Tool '{function_name}' returned: {json.dumps(result)}"
            })
        
        # Build context message with all tool results
        tool_results_summary = "\n".join([
            f"- {tr['content']}" for tr in tool_results
        ])
        
        # Continue conversation with tool results as a single message
        print(f"\n  → Calling LLM again with tool results...")
        next_prompt = f"Tool execution results:\n{tool_results_summary}\n\nNow provide your final analysis in the required JSON format."
        response = llm_caller.run(next_prompt)
    
    print(f"\n✗ Max steps ({max_steps}) reached without completion")
    return response


# Main execution
if __name__ == "__main__":
    prompt = (
        "Detect failed nodes, estimate impact, and make a report for the planner agent "
        "to be able to use this and plan for infrastructure fixes.\n"
    )
    
    final_response = run_observer_agent_with_tools(prompt, max_steps=10)
