from .dao import messages_dao
from . import background_task_executor
from ..redisdb.redisdb import get_redis
from .assistant_thread import AssistantThread
from .constants import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_INSTRUCTION
from .openai import get_openai
from .openai.datatypes import Message
from flask import current_app, g
from openai.types.beta.assistant import Assistant
from typing import Any, Literal, Optional

import json
import logging


redis = get_redis()
openai = get_openai()


class AssistantState:
    # ToDo: Change to TypedDict, move save() to AssistantService

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

    def toJSON(self):
        return json.dumps(self.state)
        
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
    def state(self) -> AssistantState:
        return self._state

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
                ASSISTANT_INSTRUCTION
            )
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

    def get_thread(self, thread_id: str = '') -> AssistantThread:
        """Retrurns the active or specified thread."""
        return AssistantThread(self.id, thread_id or self._get_active_thread_id())

    def send_message(self, text: str, thread_id: str = '',
                     *, await_response_async: bool = True) -> Message:
        thread = self.get_thread(thread_id)
        message = thread.send_message(text)
        self._logger.info(f'Sent message: {message}')

        if await_response_async:
            try:
                # Asynchronously get and save the reply
                background_task_executor.execute_concurrently(
                    thread.get_response, message['run_id'], message['id']
                )
            except Exception as e:
                self._logger.error('Failed to save response: %s', e)

        return message

    def get_messages(self,
                     thread_id: str = '',
                     *,
                     after: Optional[str] = None,
                     before: Optional[str] = None,
                     limit: Optional[int] = 20,
                     sort: Optional[Literal['asc', 'desc']] = 'desc') -> list[Message]:
        thread = self.get_thread(thread_id)
        return thread.get_messages(
            after=after, before=before, limit=limit, sort=sort)

    def get_run(self, run_id: str):
        return openai.retrieve_run(run_id, self.active_thread)

    def get_response(self, message_id: str) -> list[Message]:
        message = messages_dao.find_by_id(message_id)
        if not message:
            raise ValueError(f'No message found with id: {message_id}')
        if message['role'] != 'user':
            raise ValueError(f'Message is not from user: {message_id}')
        if not message['run_id']:
            raise ValueError(f'Message has no run_id: {message_id}')

        return self.get_thread().get_response(message['run_id'], message['id'])


def get_assistant() -> AssistantService:
    if 'assistant' not in g:
        g.assistant = AssistantService(
            current_app.config['OPENAI_ASSISTANT_ID']  # type: ignore
        )
    return g.assistant
