import os
import json
from typing import List, Dict, Any, Optional
from smolagents import OpenAIServerModel
from jsonschema import validate

class LLMConnector:
    def __init__(self, model_id: str, system_prompt: str, tools = None, messages = None, sliding_window = None, max_steps: int = 5, response_schema: Optional[Dict[str, Any]] = None):
        self.model_id = model_id
        self.base_system_prompt = system_prompt
        self.tools = tools
        self.messages = messages
        self.sliding_window = sliding_window
        self.max_steps = max_steps
        self.tool_choice = "auto" if self.tools else None
        
        # Build enhanced system prompt with schema instructions
        self.system_prompt = self.base_system_prompt
        if response_schema is not None:
            self.system_prompt = self._build_instructions(self.system_prompt, response_schema)

        # Model Ids: 
        # - "Qwen/Qwen2.5-Coder-32B-Instruct"
        self.model = OpenAIServerModel(
            model_id=self.model_id,
            api_base="https://router.huggingface.co/v1",
            api_key=os.environ["HF_TOKEN"],
            temperature=0.2,
        )
        
    def run(self, prompt: str):
        history = self.messages if self.messages is not None else []
        
        if self.sliding_window is not None and self.messages is not None:
            history = self.messages[-self.sliding_window:]

        # Build conversation with system prompt and history
        conversation = []
        
        conversation.append({"role": "system", "content": self.system_prompt})
        
        for m in history:
            conversation.append(m)
        
        # User prompt
        conversation.append({"role": "user", "content": prompt})
        
        # Prepare tools metadata
        tools_metadata = self._prepare_tools_metadata()
        
        return self.model(
            conversation, 
            tools=tools_metadata, 
            tool_choice=self.tool_choice
        )
    

    # Private Method: Helpers
    def _build_instructions(self, base_prompt: str, schema: Dict[str, Any]) -> str:
        instructions = ''
        instructions += base_prompt + "\n\n"
        if schema:
            instructions += "RESPONSE FORMAT (MANDATORY):\n"
            instructions += "You must respond ONLY with a single valid JSON object.\n"
            instructions += "Do NOT include explanations, markdown, comments, or conversational text.\n"
            instructions += "The JSON MUST strictly follow the schema below and in your response to have no json schema definitions.\n\n"
            instructions += f"{json.dumps(schema, indent=2)}\n"
        
        return instructions
    

    def _prepare_tools_metadata(self) -> Optional[List[Dict[str, Any]]]:
        """Convert SimpleTool objects to OpenAI function calling format."""
        if not self.tools:
            return None
        
        tools_metadata = []
        for tool in self.tools:
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                }
            }
            
            # Add parameters if the tool has inputs defined
            if hasattr(tool, 'inputs') and tool.inputs:
                properties = {}
                required = []
                
                for param_name, param_info in tool.inputs.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    
                    # Map Python types to JSON schema types
                    json_type = 'string'
                    if param_type in ['int', 'integer']:
                        json_type = 'integer'
                    elif param_type in ['float', 'number']:
                        json_type = 'number'
                    elif param_type in ['bool', 'boolean']:
                        json_type = 'boolean'
                    elif param_type in ['list', 'array']:
                        json_type = 'array'
                    elif param_type in ['dict', 'object']:
                        json_type = 'object'
                    
                    properties[param_name] = {
                        "type": json_type,
                        "description": param_desc
                    }
                    
                    # Check if parameter is required
                    if param_info.get('required', False):
                        required.append(param_name)
                
                tool_schema["function"]["parameters"] = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            else:
                # No parameters
                tool_schema["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            
            tools_metadata.append(tool_schema)
        
        return tools_metadata

    # Parse Response Methods
    @staticmethod
    def get_text_response(response) -> str:
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    @staticmethod
    def get_tool_calls(response) -> Optional[List[Dict[str, Any]]]:
        # First check for native OpenAI tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return response.tool_calls
        
        # Fallback: Parse tool calls from text content for models that don't support native tool_calls
        if hasattr(response, 'content') and response.content:
            try:
                content = response.content.strip()
                parsed = json.loads(content)
                
                # Check if content has function_name/function_args format (common fallback)
                if 'function_name' in parsed and 'function_args' in parsed:
                    return [{
                        'id': 'call_fallback_0',
                        'type': 'function',
                        'function': {
                            'name': parsed['function_name'],
                            'arguments': json.dumps(parsed['function_args'])
                        }
                    }]
                
                # Check if content has tool_calls array format
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
                        
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None
    
    @staticmethod
    def parse_json_response(response, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        content = LLMConnector.get_text_response(response)
        parsed = json.loads(content)
        
        if schema is not None:
            try:
                validate(instance=parsed, schema=schema)
            except ImportError:
                print("Warning: jsonschema not installed, skipping validation")
        
        return parsed