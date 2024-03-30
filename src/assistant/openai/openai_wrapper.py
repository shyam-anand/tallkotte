from .datatypes import Message
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types import FileObject
from openai.types.beta import Thread
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads import Run, ThreadMessage, MessageContentText
from typing import Optional

import logging


def _message_to_dict(message: ThreadMessage) -> dict[str, int | str | list[str] | None]:
    message_content: list[str] = []
    for content in message.content:
        if isinstance(content, MessageContentText):
            message_content.append(content.text.value)
        else:
            logging.warning(f'Unknown content type: {type(content)} {content}')
    return {
        'id': message.id,
        'role': message.role,
        'created_at': message.created_at,
        'run_id': message.run_id or None,
        'thread_id': message.thread_id,
        'content': message_content
    }


class OpenAIWrapper:

    _logger: logging.Logger = logging.getLogger(__name__)
    _client: OpenAI

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

        self._client = OpenAI(api_key=self._api_key)

    @property
    def client(self) -> OpenAI:
        return self._client

    @property
    def threads(self):
        return self.client.beta.threads

    @property
    def messages(self):
        return self.client.beta.threads.messages

    def create_assistant(
            self,
            name: str,
            description: str,
            instructions: str) -> Assistant:
        self._logger.info("Creating assistant...")

        assistant = self.client.beta.assistants.create(
            name=name, description=description, instructions=instructions, model=self._model)
        self._logger.info(f'Assistant created: {assistant.id}')
        return assistant

    def retrieve_assistant(self, assistant_id: str) -> Assistant:
        self._logger.info(f"Retrieving assistant [{assistant_id}]...")
        assistant = self.client.beta.assistants.retrieve(assistant_id)
        self._logger.info(f"Assistant: {assistant}")
        return assistant

    def open_file(self, filename: str) -> FileObject:
        file = self.client.files.create(
            file=open(filename, "rb"),
            purpose='assistants'
        )
        self._logger.info(f"File created: {file.id}")
        return file

    def create_thread(
            self, init_message: str, files: list[FileObject] = []) -> Thread:
        self._logger.info("Creating thread")
        thread = self.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": init_message,
                    "file_ids": [file.id for file in files]
                }
            ]
        )
        self._logger.info(f"Thread created: {thread.id}")
        return thread

    def retrieve_thread(self, thread_id: str) -> Thread:
        self._logger.info(f"Retrieving thread [{thread_id}]")
        thread = self.threads.retrieve(thread_id)
        self._logger.info(f"Thread: {thread}")
        return thread

    def create_message(self, thread_id: str, text: str) -> Message:
        self._logger.info(f"Creating message in thread {thread_id}: {text}")
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id, content=text, role='user')
        self._logger.info(f'Message ID: {message.id}')
        return _message_to_dict(message)

    def create_run(self, assistant_id: str, thread_id: str, instructions: str = '') -> str:
        self._logger.info(f"Running thread {
                          thread_id} in assistant {assistant_id}")
        run = self.threads.runs.create(assistant_id=assistant_id,
                                       thread_id=thread_id,
                                       instructions=instructions)
        self._logger.info(f"Run ID: {run.id}")
        return run.id

    def retrieve_run(self, run_id: str, thread_id: str) -> Run:
        self._logger.info(f'Retrieving run [{run_id}] in thread [{thread_id}]')
        run = self.threads.runs.retrieve(
            run_id=run_id, thread_id=thread_id)
        self._logger.debug(f'Run: {run}')
        return run

    def get_run_status(self, run_id: str, thread_id: str) -> str:
        run = self.retrieve_run(run_id, thread_id)
        return run.status

    def _run_info(self, run: Run) -> None:
        self._logger.debug(f'=== run.id: {run.id}')
        self._logger.debug(f'\tstatus: {run.status}')
        self._logger.debug(f'\tcreated_at: {run.created_at}')
        self._logger.debug(f'\tstarted_at: {run.started_at}')
        self._logger.debug(f'\tcompleted_at: {run.completed_at}')
        self._logger.debug(f'\tcancelled_at: {run.cancelled_at}')
        self._logger.debug(f'\texpires_at: {run.expires_at}')
        self._logger.debug(f'\tfailed_at: {run.failed_at}')
        self._logger.debug(f'\tlast_error: {run.last_error}')
        self._logger.debug(f'\trequired_action: {run.required_action}')
        usage = run.usage
        if usage:
            self._logger.debug(f'\tcompletion_tokens: {
                               usage.completion_tokens}')
            self._logger.debug(f'\tprompt_tokens: {usage.prompt_tokens}')
            self._logger.debug(f'\ttotal_tokens: {usage.total_tokens}')
        self._logger.debug('=========================')

    def list_runs(self, thread_id: str) -> SyncCursorPage[Run]:
        return self.threads.runs.list(thread_id=thread_id)

    def list_messages(self, thread_id: str, after: Optional[str] = None) -> list[Message]:
        """
        Retrieve a list of messages from a thread.

        Args:
            thread_id (str): The ID of the thread.

        Returns:
            list[Message]: Messages in the thread.
        """
        try:
            message_list = self.messages.list(thread_id=thread_id, after=after) \
                if after else self.messages.list(thread_id=thread_id)
        except Exception as e:
            self._logger.error(f"Error retrieving messages: {e}")
            return []

        return [_message_to_dict(message) for message in message_list]
