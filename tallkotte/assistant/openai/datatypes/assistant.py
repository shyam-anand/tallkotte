from openai.types.beta.assistant import Assistant as OpenAiAssistant
from typing import Any, Mapping, Optional, TypedDict, Union

import json
import logging


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


def to_assistant(convert_from: OpenAiAssistant | dict[str, Any] | Mapping[str, Any]) -> Assistant:
    return _from_openai_assistant(convert_from) \
        if isinstance(convert_from, OpenAiAssistant) \
        else _from_dict(convert_from)


def _from_openai_assistant(openai_assistant: OpenAiAssistant) -> Assistant:
    logging.info(f'Converting from OpenAiAssistant: {openai_assistant}')
    assistant = Assistant(
        id=openai_assistant.id,
        name=openai_assistant.name,
        instructions=openai_assistant.instructions,
        tools=[tool.type for tool in openai_assistant.tools],
        threads=[],
        active_thread=''
    )
    logging.info(f'Created Assistant: {assistant}')
    return assistant


def _from_dict(assistant_object: dict[str, Any] | Mapping[str, Any]) -> Assistant:
    logging.info(f'Converting from {type(assistant_object)}: '
                 f'{assistant_object}')
    assistant_attributes = {
        'id': assistant_object['id'],
        'name': assistant_object['name'],
        'instructions': assistant_object['instructions'],
        'tools': assistant_object['tools'],
    }

    assistant_attributes['threads'] = assistant_object['threads'] \
        if 'threads' in assistant_object \
        else []
    assistant_attributes['active_thread'] = assistant_object['active_thread'] \
        if 'active_thread' in assistant_object \
        else ''

    assistant = Assistant(**assistant_attributes)
    logging.info(f'Created Assistant: {assistant}')
    return assistant
