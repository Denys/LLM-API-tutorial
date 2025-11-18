"""Exercise Solution: Tool Call Validation System.

Pydantic models for defining and validating LLM tool calls.

Run: python exercise_solution.py
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any
import json


class Tool(BaseModel):
    """Definition of a tool that can be called by the LLM."""

    name: str = Field(min_length=1, description="Tool name (alphanumeric + underscore)")
    description: str = Field(min_length=1, description="What the tool does")
    input_schema: dict = Field(description="JSON Schema for input parameters")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is valid identifier."""
        if not v.replace('_', '').isalnum():
            raise ValueError("Name must be alphanumeric with underscores only")
        if v[0].isdigit():
            raise ValueError("Name cannot start with a digit")
        return v


class ToolCall(BaseModel):
    """A tool call from the LLM."""

    id: str = Field(description="Unique tool use ID")
    name: str = Field(description="Name of tool to call")
    input: dict = Field(description="Input parameters")

    def validate_against_tools(self, tools: list[Tool]) -> tuple[bool, str]:
        """Validate this tool call against available tools.

        Args:
            tools: List of available tool definitions.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Find matching tool
        matching_tools = [t for t in tools if t.name == self.name]

        if not matching_tools:
            available = [t.name for t in tools]
            return False, f"Unknown tool '{self.name}'. Available: {available}"

        tool = matching_tools[0]

        # Validate required parameters
        schema = tool.input_schema
        required = schema.get('required', [])
        properties = schema.get('properties', {})

        for param in required:
            if param not in self.input:
                return False, f"Missing required parameter: {param}"

        # Check for unknown parameters
        for param in self.input:
            if param not in properties:
                return False, f"Unknown parameter: {param}"

        return True, ""


class ToolResult(BaseModel):
    """Result of executing a tool."""

    tool_use_id: str = Field(description="ID of the tool call this is responding to")
    success: bool = Field(description="Whether execution succeeded")
    output: Any = Field(default=None, description="Tool output on success")
    error: str | None = Field(default=None, description="Error message on failure")

    @model_validator(mode='after')
    def check_output_or_error(self):
        """Ensure output or error is set appropriately."""
        if self.success and self.output is None:
            raise ValueError("Successful result must have output")
        if not self.success and self.error is None:
            raise ValueError("Failed result must have error message")
        return self


def validate_tool_call(
    tool_call: ToolCall,
    available_tools: list[Tool]
) -> ToolResult:
    """Validate a tool call and return validation result.

    Args:
        tool_call: The tool call to validate.
        available_tools: List of available tools.

    Returns:
        ToolResult indicating validation outcome.
    """
    is_valid, error_msg = tool_call.validate_against_tools(available_tools)

    if is_valid:
        return ToolResult(
            tool_use_id=tool_call.id,
            success=True,
            output={"validated": True, "tool": tool_call.name}
        )
    else:
        return ToolResult(
            tool_use_id=tool_call.id,
            success=False,
            error=f"Validation failed: {error_msg}"
        )


if __name__ == "__main__":
    # Define some tools
    tools = [
        Tool(
            name="get_weather",
            description="Get current weather for a location",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        ),
        Tool(
            name="calculator",
            description="Perform math operations",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            }
        )
    ]

    print("Available tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()

    # Test valid tool call
    print("Testing valid tool call:")
    valid_call = ToolCall(
        id="call_123",
        name="get_weather",
        input={"location": "San Francisco", "unit": "celsius"}
    )
    result = validate_tool_call(valid_call, tools)
    print(f"  {valid_call.name}({valid_call.input})")
    print(f"  Result: success={result.success}")
    print()

    # Test invalid tool call (unknown tool)
    print("Testing invalid tool (unknown):")
    invalid_call = ToolCall(
        id="call_456",
        name="unknown_tool",
        input={}
    )
    result = validate_tool_call(invalid_call, tools)
    print(f"  {invalid_call.name}({invalid_call.input})")
    print(f"  Result: success={result.success}, error={result.error}")
    print()

    # Test invalid tool call (missing required param)
    print("Testing invalid tool (missing param):")
    missing_param = ToolCall(
        id="call_789",
        name="calculator",
        input={"operation": "add", "a": 5}  # Missing 'b'
    )
    result = validate_tool_call(missing_param, tools)
    print(f"  {missing_param.name}({missing_param.input})")
    print(f"  Result: success={result.success}, error={result.error}")
