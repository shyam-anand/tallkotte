from openai.types.beta.assistant import Assistant as OpenAiAssistant
from typing import Any, Optional, TypedDict, Union
import json


class Assistant(TypedDict):
    # ToDo: Change to TypedDict, move save() to AssistantService
    id: str
    name: str | None
    instructions: str | None
    tools: list[str]
    threads: list[str]
    active_thread: str


class AssistantState:
    def __init__(self, id: str, state: Assistant):
        self._id = id
        self._state = state

    @property
    def state(self) -> Assistant:
        return self._state

    def set(self, key: str, value: str | list[str]):
        self.state[key] = value

    def get(self, key: str, default: Union[Optional[str], Optional[list[str]]] = None) -> str | list[str]:
        return self.state.get(key, default)


def toJSON(assistant: Assistant):
    return json.dumps(assistant)


def to_assistant(convert_from: OpenAiAssistant | dict[str, Any]) -> Assistant:
    if isinstance(convert_from, OpenAiAssistant):
        return _from_openai_assistant(convert_from)
    return _from_dict(convert_from)


def _from_openai_assistant(openai_assistant: OpenAiAssistant) -> Assistant:
    return Assistant(
        id=openai_assistant.id,
        name=openai_assistant.name,
        instructions=openai_assistant.instructions,
        tools=[tool.type for tool in openai_assistant.tools],
        threads=[],
        active_thread=''
    )


def _from_dict(assistant_object: dict[str, Any]) -> Assistant:
    return Assistant(
        id=assistant_object['id'],
        name=assistant_object['name'],
        instructions=assistant_object['instructions'],
        tools=assistant_object['tools'],
        threads=[],
        active_thread=''
    )
