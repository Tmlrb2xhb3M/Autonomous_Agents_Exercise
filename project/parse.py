import json
from jsonschema import validate, ValidationError


class LLMOutputParsingError(Exception):
    """Raised when LLM output is not valid JSON or does not match schema."""
    pass


def parse_llm_output(raw_output: str, schema: dict) -> dict:
    """
    Parses and validates LLM output.

    Args:
        raw_output (str): Raw string output from the LLM.
        schema (dict): JSON Schema to validate against.

    Returns:
        dict: Parsed and validated JSON object.

    Raises:
        LLMOutputParsingError: If parsing or validation fails.
    """
    # JSON parsing
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise LLMOutputParsingError(
            f"LLM returned invalid JSON:\n{raw_output}"
        ) from e

    # Schema validation
    try:
        validate(instance=parsed, schema=schema)
    except ValidationError as e:
        raise LLMOutputParsingError(
            f"LLM JSON does not match schema:\n{e.message}"
        ) from e

    return parsed
