from . import background_task_executor
from ..datastore.redisdb.redisdb import get_redis
from ..datastore.mongodb.mongo_wrapper import MongoDB, get_mongo
from .assistant_thread import AssistantThread
from .constants import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_INSTRUCTION
from .dao import assistants_dao, messages_dao
from .openai.datatypes.assistant import Assistant
from .openai.datatypes.message import Message
from .openai.openai_wrapper import get_openai
from flask import current_app, g
from typing import Any, Literal, Mapping, Optional

import logging


mongodb: MongoDB[Mapping[str, Any]] = get_mongo()
openai = get_openai()
redis = get_redis()


def _create_assistant(name: str = ASSISTANT_NAME,
                      description: str = ASSISTANT_DESCRIPTION,
                      instruction: str = ASSISTANT_INSTRUCTION) -> Assistant:
    assistant = openai.create_assistant(
        name, description, instruction)
    return assistants_dao.save(assistant)


def _retrieve_assistant(assistant_id: str) -> Assistant:
    def get_thread_ids(assistant_id: str) -> list[str]:
        results: list[Mapping[str, str]] = mongodb.find(
            'threads', {'assistant_id': assistant_id}, {'id': 1})
        logging.info(f'Found {len(results)} threads')
        return [result['id'] for result in results]

    assistant_state = assistants_dao.get(assistant_id)
    if not assistant_state:
        assistant = openai.retrieve_assistant(assistant_id)
        if not assistant:
            raise ValueError(f'No assistant found with id: {assistant_id}')
        assistant['threads'] = get_thread_ids(assistant['id'])
        return assistants_dao.save(assistant)

    return assistant_state


class AssistantService:

    _logger = logging.getLogger(__name__)

    _state: Assistant

    def __init__(self, assistant_id: Optional[str] = None,
                 *, create_new: bool = False):
        if assistant_id:
            self._state = _retrieve_assistant(assistant_id)
        elif create_new:
            self._state = _create_assistant()
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

    def _add_thread(self, thread_id: str,
                    *, set_active: bool = True):
        self._logger.info(f'About to update state: {self._state}')
        self._state['threads'].append(thread_id)
        if set_active:
            self._state['active_thread'] = thread_id

        assistants_dao.save(self._state)
        self._logger.info(
            f'Added {thread_id} to assistant {self.id}')

    def create_thread(self,
                      *,
                      cv_files: list[str] = [],
                      init_message: Optional[str] = None,
                      set_active: bool = True) -> AssistantThread:
        files = [
            openai.open_file(filename)
            for filename in cv_files
        ]
        thread = AssistantThread(self.id,
                                 files=files,
                                 init_message=init_message,
                                 create_new=True)

        self._add_thread(thread.id, set_active=set_active)

        return thread

    def get_thread(self, thread_id: str = '',
                   *,
                   create_thread: bool = False) -> AssistantThread:
        """Retrurns the active or specified thread."""
        if thread_id:
            return AssistantThread(self.id, thread_id)
        elif self.active_thread:
            return AssistantThread(self.id, self.active_thread)
        elif create_thread:
            return self.create_thread()

        raise ValueError(f'No thread found with id: {thread_id}')

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
