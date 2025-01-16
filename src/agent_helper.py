import inspect
from typing import Annotated, get_origin, get_args
from enum import Enum
from pydantic import BaseModel


def function_to_schema(func) -> dict:
    """
    Converts a Python function into a schema suitable for OpenAI tools.

    Args:
        func (callable): The function to convert.

    Returns:
        dict: Schema for the function.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    parameters = {}
    signature = inspect.signature(func)

    for name, param in signature.parameters.items():
        # Skip *args and **kwargs
        if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue

        annotation = param.annotation
        param_schema = {}

        # Check if the annotation is Annotated
        if get_origin(annotation) is Annotated:
            # Extract base type and metadata
            base_type, *metadata = get_args(annotation)
            param_schema["type"] = type_map.get(base_type, "string")

            # Process metadata
            for meta in metadata:
                if isinstance(meta, str):  # Description
                    param_schema["description"] = meta
            # Handle Enum within Annotated
            if isinstance(base_type, type) and issubclass(base_type, Enum):
                param_schema["enum"] = [item.value for item in base_type]

        # Handle Enum types without Annotated
        elif isinstance(annotation, type) and issubclass(annotation, Enum):
            param_schema["type"] = "string"
            param_schema["enum"] = [item.value for item in annotation]

        # Handle basic types
        else:
            param_schema["type"] = type_map.get(annotation, "string")

        parameters[name] = param_schema

    # Identify required parameters (those without defaults), skipping *args and **kwargs
    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
        and param.kind not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
                "additionalProperties": False
            },
        },
    }


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: str = "You are a helpful Agent"
    tools: list = None
    tool_map: dict = {}

    def __init__(self, **data):
        functions = data.get("functions")
        super().__init__(**data)  # Call Pydantic's constructor
        if functions and len(functions) > 0:
            self.tools = []
            for func in functions:
                self.tools.append(function_to_schema(func))
                self.tool_map[func.__name__] = func

    def add_tool(self, func):
        tool = function_to_schema(func)
        if not self.tools:
            self.tools = []
        self.tools.append(tool)
        self.tool_map[func.__name__] = func
