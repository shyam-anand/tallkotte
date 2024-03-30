from .assistant_thread import AssistantThread
from .constants import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_INSTRUCTION
from .openai import openai
from .openai.datatypes import Message
from ..redisdb import redis
from openai.types.beta.assistant import Assistant
from typing import Any, Optional

import asyncio
import json
import logging


class AssistantState:
    def __init__(self, id: str, state: dict[str, Any]):
        self._id = id
        self._state = state

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    def set(self, key: str, value: Any):
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def save(self):
        state = json.dumps(self.state)
        logging.info(f'Saving state {self._id}: {state}')
        redis.write(self._id, state)


def save_assistant(assistant: Assistant) -> AssistantState:
    assistant_state = AssistantState(
        assistant.id,
        {
            'id': assistant.id,
            'name': assistant.name,
            'instructions': assistant.instructions,
            'tools': [tool.type for tool in assistant.tools],
            'threads': [],
            'active_thread': ''
        }
    )
    assistant_state.save()

    return assistant_state


class AssistantService:

    _logger = logging.getLogger(__name__)

    def __init__(self, assistant_id: Optional[str] = None):
        self._state = self._retrieve(assistant_id) if assistant_id \
            else self._create()

    @property
    def id(self) -> str:
        return self._state.get('id')

    @property
    def name(self) -> str:
        return self._state.get('name')

    @property
    def threads(self) -> list[str]:
        return self._state.get('threads')

    @property
    def active_thread(self) -> str:
        return self._state.get('active_thread')

    def _create(self) -> AssistantState:
        return save_assistant(
            openai.create_assistant(
                ASSISTANT_NAME,
                ASSISTANT_DESCRIPTION,
                ASSISTANT_INSTRUCTION)
        )

    def _retrieve(self, assistant_id: str) -> AssistantState:
        assistant_json = redis.read(assistant_id)
        if assistant_json:
            assistant_state = json.loads(assistant_json)
            return AssistantState(assistant_state['id'], assistant_state)

        assistant = openai.retrieve_assistant(assistant_id)
        if not assistant:
            raise ValueError(f'No assistant found with id: {assistant_id}')

        return save_assistant(assistant)

    def _set_active_thread(self, thread_id: str):
        self._logger.info(
            f"Setting active thread {thread_id} for assistant {self.id}")

        self._state.set('active_thread', thread_id)
        if thread_id not in self.threads:
            self.threads.append(thread_id)

        self._state.save()

    def _get_active_thread_id(self) -> Optional[str]:
        if not self.active_thread:
            if len(self.threads) > 0:
                active_thread = self.threads[0]
                self._set_active_thread(active_thread)

        return self.active_thread

    def create_thread(self,
                      cv_files: list[str],
                      set_active: bool = True) -> AssistantThread:
        files = [
            openai.open_file(filename)
            for filename in cv_files
        ]
        thread = AssistantThread(self.id, files=files)
        if set_active:
            self._set_active_thread(thread.id)

        return thread

    def get_thread(self, thread_id: Optional[str]) -> AssistantThread:
        """Retrurns the active or specified thread."""
        return AssistantThread(self.id, thread_id or self._get_active_thread_id())

    async def _save_response(self, thread: AssistantThread, message: Message) -> None:
        thread.save_response(message.run_id, message.id)

    def send_message(self, text: str, thread_id: str = '') -> Message:
        thread: AssistantThread = self.get_thread(thread_id or None)
        message = thread.send_message(text)

        try:
            # Asynchronously get and save the reply
            asyncio.run(self._save_response(thread, message))
        except Exception as e:
            self._logger.error('Failed to save response: %s', e)

        self._logger.info(f'Sent message: {message}')
        return message
