from ..datastore.cachedstore import CachedStore
from ..datastore.mongodb.mongo_query import MongoQueryBuilder
from ..datastore.redisdb.redisdb import get_redis
from .constants import ASSISTANT_INIT_MESSAGE
from .dao import messages_dao
from .openai.datatypes.message import Message
from .openai.openai_wrapper import get_openai
from openai.types import FileObject
from openai.types.beta import Thread as OpenAiThread
from typing import Literal, Optional, TypedDict

import json
import logging
import time


class Thread(TypedDict):
    id: str
    assistant_id: str
    created_at: int


redis = get_redis()
openai = get_openai()
cached_store = CachedStore[Thread](
    'threads', lambda thread_map: Thread(**thread_map))


class AssistantThread:

    _logger = logging.getLogger(__name__)

    def __init__(self,
                 assistant_id: str,
                 thread_id: Optional[str] = None,
                 files: list[FileObject] = [],
                 init_message: Optional[str] = None,
                 *,
                 create_new: bool = False) -> None:
        if not assistant_id:
            raise ValueError('assistant_id is required')

        if thread_id:
            self._state = self._get(assistant_id, thread_id)
        elif create_new:
            init_message = init_message or ASSISTANT_INIT_MESSAGE
            self._state = self._create(assistant_id, files, init_message)
        else:
            raise ValueError(
                'thread_id must be specified, or create_new must be True')

    @property
    def id(self) -> str:
        return self._state['id']

    @property
    def assistant_id(self) -> str:
        return self._state['assistant_id']

    def _save(self, opeanai_thread: OpenAiThread, assistant_id: str) -> Thread:
        thread = Thread(id=opeanai_thread.id,
                        assistant_id=assistant_id,
                        created_at=opeanai_thread.created_at)

        cached_store.write_one(thread)
        self._logger.info(f'Thread saved: {thread}')
        return thread

    def _get(self, assistant_id: str, thread_id: str) -> Thread:
        self._logger.info(f'Reading: {thread_id}')
        thread = cached_store.read(thread_id,
                                   MongoQueryBuilder(id=thread_id).build())
        if not thread:
            return self._save(openai.retrieve_thread(thread_id), assistant_id)

        return thread[0] if isinstance(thread, list) \
            else thread

    def _create(self,
                assistant_id: str,
                files: list[FileObject] = [],
                init_message: str = ASSISTANT_INIT_MESSAGE) -> Thread:
        return self._save(
            openai.create_thread(
                files=files, init_message=init_message),
            assistant_id
        )

    def _get_last_message(self, thread_id: str) -> Message | None:
        """Get last message in thread from Mongo."""
        results = messages_dao.find(
            filter={'thread_id': thread_id},
            sort={'timestamp': -1}
        )

        return results[0] if results else None

    def send_message(self, text: str) -> Message:
        """Send a message to the thread.

        Creates a new message in the thread, then creates run in the thread.
        The created message is saved in the database, and returned.

        Args:
            text (str): Text to send.

        Returns:
            Message: The created message, with the run_id.
        """
        message = openai.create_message(self.id, text)
        self._logger.info(f'Message {message['id']} added to thread {self.id}')

        run = openai.create_run(self.assistant_id, self.id)
        run_id = run['id']
        redis.write(f'{run_id}:status', 'created')
        self._logger.info(f'{run_id} created in {self.id}')

        # Set run_id in message
        message['run_id'] = run_id

        self._logger.debug(f'Saving message: {message}')
        messages_dao.save([message])
        redis.write(f'last_sent:{self.id}', json.dumps(message['id']))

        return message

    def _await_run_completion(self, run_id: str,
                              wait_delay: int = 2,
                              max_wait_sec: int = 60) -> None:
        """Blocks until run is completed."""

        # Check if the run was previously completed.
        run_status = redis.read(f'{run_id}:status')
        if bool(run_status and run_status == 'completed'):
            return

        def run_incomplete() -> bool:
            run_status = openai.get_run_status(run_id, self.id)
            self._logger.info(f'Run status: {run_status}')
            return run_status in ['queued', 'in_progress', 'cancelling']

        self._logger.debug(f'Awaiting completion of run [{run_id}]')
        end = start = time.time()

        while run_incomplete() and (end - start) < max_wait_sec:
            self._logger.info(f'Waiting {wait_delay} seconds')
            time.sleep(wait_delay)
            end = time.time()

        if (end - start) > max_wait_sec:
            redis.write(f'{run_id}:status', 'timeout')
            raise RuntimeError(
                f'Run not completed after {max_wait_sec} seconds')

        self._logger.debug('Run completed: %s', run_id)
        redis.write(f'{run_id}:status', 'completed')

    def _get_saved_response(self, run_id: str) -> Optional[list[Message]]:
        return messages_dao.find_by_run_id_and_role(run_id, 'assistant')

    def _await_run_completion_and_get_response(
            self, run_id: str, user_message_id: str) -> list[Message]:
        self._await_run_completion(run_id)

        messages = self.get_messages(before=user_message_id)

        response: list[Message] = []
        for message in messages:
            if not messages_dao.find({'id': message['id']}):
                message['run_id'] = run_id
                response.append(message)

        self._logger.info(f'Saving {len(response)} responses.')
        messages_dao.save(response)

        self._logger.info('Response for %s retrieved', user_message_id)
        self._logger.info(response)

        return response

    def get_response(self, run_id: str, user_message_id: str) -> list[Message]:
        """Get response messages from the run, after the given message ID.

        If the Run is not complete, wait until it is. Then fetch the messages 
        in the thread. If 'after' is specified, messages after that message
        will be returned.

        Args:
            run_id (str): Run ID for which to get messages.
            after (str): Message ID after which to get messages.

        Returns:
            List of messages from the run.
        """
        self._logger.info('Retrieving response for %s', user_message_id)

        return self._get_saved_response(run_id) \
            or self._await_run_completion_and_get_response(
                run_id, user_message_id)

    def get_messages(
            self, *,
            before: Optional[str] = None,
            after: Optional[str] = None,
            limit: Optional[int] = None,
            sort: Optional[Literal['asc', 'desc']] = 'desc') -> list[Message]:
        """Get messages for the thread.

        For details of args, refer :py:meth:`openai.OpenAIWrapper.list_messages`.
        """
        self._logger.debug('Retrieving messages for thread: %s%s',
                           self.id, f'after {after}' if after else '')

        messages = openai.list_messages(self.id,
                                        before=before,
                                        after=after,
                                        limit=limit or 20,
                                        sort=sort)
        self._logger.info(f'{len(messages)} messages retrieved')
        return messages
