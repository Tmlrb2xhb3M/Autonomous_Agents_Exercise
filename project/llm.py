import os
import json
from smolagents import ToolCallingAgent, OpenAIServerModel
from smolagents.monitoring import LogLevel

model = OpenAIServerModel(
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    api_base="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
    tool_choice="auto",
    temperature=0.2,
)

def llm_call(system_prompt: str, prompt: str, tools=[], messages=None, sliding_window = None, max_steps: int = 10) -> ToolCallingAgent.Result:
    agent = ToolCallingAgent(
        model=model,
        tools=tools,
        return_full_result=True,
        verbosity_level=LogLevel.ERROR
    )

    history = messages

    if messages is None:
        history = []

    if sliding_window is not None:
        history = messages[-sliding_window:]

    history_text = system_prompt + "\n\n"
    for m in history:
        role = m.get("role", "user").upper()
        content = m.get("content", "")
        history_text += f"{role}:\n{content}\n\n"

    full_prompt = history_text + "TASK:\n" + prompt

    result = agent.run(
        full_prompt,
        max_steps=max_steps,
    )

    return result
