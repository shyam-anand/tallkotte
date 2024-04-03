from . import background_task_executor
from ..datastore.redisdb.redisdb import get_redis
from .assistant_thread import AssistantThread
from .constants import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_INSTRUCTION
from .dao import assistants_dao, messages_dao
from .openai.datatypes.assistant import Assistant, to_assistant
from .openai.datatypes.message import Message
from .openai.openai_wrapper import get_openai
from flask import current_app, g
from typing import Literal, Optional

import logging


redis = get_redis()
openai = get_openai()


class AssistantService:

    _logger = logging.getLogger(__name__)

    def __init__(self, assistant_id: Optional[str] = None, create_new: bool = False):
        if assistant_id:
            self._state = self._retrieve(assistant_id)
        elif create_new:
            self._create()
        else:
            raise ValueError('No assistant id provided')

    @property
    def state(self) -> Assistant:
        return self._state

    @property
    def id(self) -> str:
        return self._state['id']

    @property
    def name(self) -> str | None:
        return self._state['name']

    @property
    def threads(self) -> list[str]:
        return self._state['threads']

    @property
    def active_thread(self) -> str:
        return self._state['active_thread']

    def _create(self) -> Assistant:
        openai_assistant = openai.create_assistant(
            ASSISTANT_NAME,
            ASSISTANT_DESCRIPTION,
            ASSISTANT_INSTRUCTION
        )
        return assistants_dao.save(to_assistant(openai_assistant))

    def _retrieve(self, assistant_id: str) -> Assistant:
        assistant_state = assistants_dao.get(assistant_id)
        if assistant_state:
            return assistant_state

        assistant = openai.retrieve_assistant(assistant_id)
        if not assistant:
            raise ValueError(f'No assistant found with id: {assistant_id}')

        return assistants_dao.save(to_assistant(assistant))

    def _set_active_thread(self, thread_id: str):
        self._logger.info(
            f"Setting active thread {thread_id} for assistant {self.id}")

        self._state['active_thread'] = thread_id
        if thread_id not in self.threads:
            self.threads.append(thread_id)

        assistants_dao.save(self._state)

    def _get_active_thread_id(self) -> Optional[str]:
        if not self.active_thread:
            if len(self.threads) > 0:
                active_thread = self.threads[0]
                self._set_active_thread(active_thread)

        return self.active_thread

    def create_thread(self,
                      cv_files: list[str] = [],
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
        if thread_id:
            return AssistantThread(self.id, thread_id)
        elif self.active_thread:
            return AssistantThread(self.id, self.active_thread)

        return self.create_thread()

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
    logging.info('Initializing assistant')
    if 'assistant' not in g:
        assistant_id = current_app.config.get('ASSISTANT_ID')  # type: ignore
        logging.info(f'Instantiating assistant [assisant_id="{assistant_id}"]')
        g.assistant = AssistantService(
            assistant_id=assistant_id)  # type: ignore
    return g.assistant
