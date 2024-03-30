from .constants import ASSISTANT_INIT_MESSAGE
from .openai import openai
from .openai.datatypes import Message
from ..mongodb import mongodb
from ..redisdb import redis
from openai.types import FileObject
from openai.types.beta import Thread
from typing import Any, Optional

import json
import logging
import time


def _to_message(message_document: dict[str, Any]) -> Message:
    return Message(
        message_document['id'],
        message_document['role'],
        message_document['created_at'],
        message_document['run_id'],
        message_document['thread_id'],
        message_document['content']
    )


class AssistantThread:

    _logger = logging.getLogger(__name__)

    _id: str = ''

    def __init__(self,
                 assistant_id: str,
                 thread_id: Optional[str] = None,
                 files: list[FileObject] = []) -> None:
        if not assistant_id:
            raise ValueError('assistant_id is required')

        self._assistant_id = assistant_id
        self._init_thread(thread_id=thread_id, files=files)

    def _init_thread(self,
                     thread_id: Optional[str],
                     files: list[FileObject] = [],
                     init_message: str = ASSISTANT_INIT_MESSAGE,) -> None:
        def _save(thread: Thread) -> dict[str, str | list[str]]:
            thread_json: dict[str, str | list[str]] = {
                'id': thread.id,
                'runs': []
            }
            redis.write(thread.id, json.dumps(thread_json))
            return thread_json

        thread = (
            self._get(thread_id) or _save(
                openai.retrieve_thread(self._assistant_id))
        ) if thread_id else (
            _save(
                openai.create_thread(
                    files=files, init_message=init_message)
            )
        )

        self._id = thread['id']  # type: ignore

    def _save(self, thread: Thread) -> dict[str, Any]:
        thread_json: dict[str, Any] = {
            'id': thread.id,
            'runs': []
        }
        redis.write(thread.id, json.dumps(thread_json))
        self._logger.info(f'Thread saved: {thread.id}')
        return thread_json

    def _get(self, thread_id: str):
        self._logger.info(f'Reading: {thread_id}')
        thread_json = redis.read(thread_id)
        return json.loads(thread_json) if thread_json else None

    @property
    def id(self) -> str:
        return self._id

    def _save_messages(self, messages: list[Message]) -> None:
        try:
            insert_ids = mongodb.insert('messages', messages)
            self._logger.info(f'{len(insert_ids)} messages inserted')
            self._logger.info([str(o) for o in insert_ids])
        except Exception as e:
            self._logger.error(f'Error while saving messages: {e}')

    def _find_messages_by_run_id(self, run_id: str) -> list[Message]:
        try:
            results = mongodb.find('messages', {'run_id': run_id})
            return [_to_message(document) for document in results]
        except Exception as e:
            self._logger.error(f'Error while retrieving messages: {e}')
            return []

    def _run_complete(self, run_id: str) -> bool:
        cached_run_status = redis.read(f'{run_id}:status')
        return bool(cached_run_status and cached_run_status == 'completed')

    def _await_run_completion(self, run_id: str,
                              wait_delay: int = 2,
                              max_wait_sec: int = 60) -> None:
        """Blocks until run is completed."""
        def run_incomplete() -> bool:
            run_status = openai.get_run_status(run_id, self.id)
            return run_status in ['queued', 'in_progress', 'cancelling']

        self._logger.debug('Awaiting run completion: %s', run_id)
        end = start = time.time()

        while run_incomplete() and (end - start) < max_wait_sec:
            time.sleep(wait_delay)
            end = time.time()

        if (end - start) > max_wait_sec:
            redis.write(f'{run_id}:status', 'timeout')
            raise RuntimeError(f'Run not completed after {
                               max_wait_sec} seconds')

        self._logger.debug('Run completed: %s', run_id)
        redis.write(f'{run_id}:status', 'completed')

    def _get_last_message(self, thread_id: str) -> Message | None:
        """Get last message in thread from Mongo."""
        results = mongodb.find(
            'messages',
            filter={'thread_id': thread_id},
            sort={'timestamp': -1}
        )

        if len(results) >= 1:
            return _to_message(results[0])

        return None

    def get_messages(self, after: str = '') -> list[Message]:
        self._logger.debug('Retrieving messages for current thread: %s%s',
                           self.id, f'after {after}' if after else '')
        messages = openai.list_messages(self.id, after=after)
        self._logger.info(f'{len(messages)} messages retrieved')

        return messages

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
        self._logger.info(f'Message added: {message.id}')

        run_id = openai.create_run(
            self._assistant_id, self.id)
        redis.write('f{run_id}:status', 'created')
        self._logger.info(f'Run created: {run_id}')

        # Set run_id in message
        message.run_id = run_id

        self._save_messages([message])
        redis.write(f'last_sent:{self.id}', json.dumps(message))

        return message

    def save_response(self, run_id: str, message_id: str) -> None:
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
        def _get_messages(run_id: str, after: str) -> list[Message]:
            # If the run was previously cancelled, fetch the messages from the database.
            if self._run_complete(run_id):
                return self._find_messages_by_run_id(run_id)

            self._await_run_completion(run_id)
            return self.get_messages(after=after)

        response = _get_messages(run_id, message_id)
        self._save_messages(response)
        redis.write(f'reply:{message_id}', json.dumps(response))

        self._logger.info('Replies for %s retrieved and saved', message_id)
        self._logger.info(response)
