import os
import json
from typing import List, Dict, Any, Optional
from smolagents import InferenceClientModel
from jsonschema import validate

class LLMConnector:
    def __init__(self, model_id: str, system_prompt: str, tools = None, messages = None, sliding_window = None, max_steps: int = 5, response_schema: Optional[Dict[str, Any]] = None):
        self.model_id = model_id
        self.base_system_prompt = system_prompt
        self.response_schema = response_schema
        self.tools = tools
        self.messages = messages
        self.initial_messages = messages.copy() if messages else []
        self.initial_message_count = len(self.initial_messages)
        self.sliding_window = sliding_window
        self.max_steps = max_steps
        
        self.system_prompt = self._build_instructions()
        
        self.model = InferenceClientModel(
            model_id=self.model_id,
            token=os.environ.get("HF_TOKEN"),
            timeout=120,
        )
        
    def run(self, prompt: str):
        history = self.messages if self.messages is not None else []
        
        if self.sliding_window is not None and len(history) > self.initial_message_count:
            additional_messages = history[self.initial_message_count:]
            if len(additional_messages) > self.sliding_window:
                additional_messages = additional_messages[-self.sliding_window:]
            history = self.initial_messages + additional_messages
        
        conversation = []
        
        conversation.append({
            "role": "system", 
            "content": [{"type": "text", "text": self.system_prompt}]
        })
        
        for m in history:
            conversation.append(m)
        
        conversation.append({
            "role": "user", 
            "content": [{"type": "text", "text": prompt}]
        })  

        if self.tools and len(self.tools) > 0:
            return self.model(
                conversation, 
                tools_to_call_from=self.tools,
                tool_choice="auto"
            )
        else:
            return self.model(conversation)
    
    def _build_instructions(self) -> str:
        instructions = self.base_system_prompt
        
        if self.response_schema:
            instructions += "\n\nRESPONSE FORMAT:\nRespond with valid JSON matching this schema:\n"
            instructions += json.dumps(self.response_schema, indent=2)
            instructions += "\n\nIMPORTANT:\n- Follow the schema strictly"
            instructions += "\n- Include all required fields"
            instructions += "\n- Use correct data types"
            instructions += "\n- Respond with ONLY the JSON object"
        
        return instructions

    # Parse Response Methods
    @staticmethod
    def get_text_response(response) -> str:
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    @staticmethod
    def get_tool_calls(response) -> Optional[List[Dict[str, Any]]]:
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return response.tool_calls
        
        if hasattr(response, 'content') and response.content:
            try:
                content = response.content.strip()
                
                try:
                    parsed = json.loads(content)
                    
                    if 'name' in parsed and 'arguments' in parsed:
                        return [{
                            'id': 'call_fallback_0',
                            'type': 'function',
                            'function': {
                                'name': parsed['name'],
                                'arguments': json.dumps(parsed['arguments']) if isinstance(parsed['arguments'], dict) else parsed['arguments']
                            }
                        }]
                    
                    if 'function_name' in parsed and 'function_args' in parsed:
                        return [{
                            'id': 'call_fallback_0',
                            'type': 'function',
                            'function': {
                                'name': parsed['function_name'],
                                'arguments': json.dumps(parsed['function_args'])
                            }
                        }]
                    
                    if 'tool_calls' in parsed and isinstance(parsed['tool_calls'], list):
                        tool_calls = []
                        for idx, tc in enumerate(parsed['tool_calls']):
                            if 'tool_name' in tc:
                                tool_calls.append({
                                    'id': f'call_fallback_{idx}',
                                    'type': 'function',
                                    'function': {
                                        'name': tc['tool_name'],
                                        'arguments': json.dumps(tc.get('parameters', {}))
                                    }
                                })
                        if tool_calls:
                            return tool_calls
                
                except json.JSONDecodeError:
                    lines = content.strip().split('\n')
                    tool_calls = []
                    
                    for idx, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            parsed = json.loads(line)
                            
                            # Check for name/arguments format
                            if 'name' in parsed and 'arguments' in parsed:
                                tool_calls.append({
                                    'id': f'call_fallback_{idx}',
                                    'type': 'function',
                                    'function': {
                                        'name': parsed['name'],
                                        'arguments': json.dumps(parsed['arguments']) if isinstance(parsed['arguments'], dict) else parsed['arguments']
                                    }
                                })
                            # Check for function_name/function_args format
                            elif 'function_name' in parsed and 'function_args' in parsed:
                                tool_calls.append({
                                    'id': f'call_fallback_{idx}',
                                    'type': 'function',
                                    'function': {
                                        'name': parsed['function_name'],
                                        'arguments': json.dumps(parsed['function_args'])
                                    }
                                })
                        except json.JSONDecodeError:
                            continue
                    
                    if tool_calls:
                        return tool_calls
                        
            except (KeyError, Exception):
                pass
                pass
        
        return None
    
    @staticmethod
    def parse_json_response(response, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        content = LLMConnector.get_text_response(response)
        parsed = json.loads(content)
        
        if schema is not None:
            validate(instance=parsed, schema=schema)
        
        return parsed