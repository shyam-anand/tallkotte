from .datatypes.run import Run
from . import converters
from .datatypes.message import Message
from flask import current_app, g
from openai import OpenAI
from openai.types import FileObject
from openai.types.beta import Thread
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads import Run as OpenAIRun
from typing import Literal, Optional
import logging


class OpenAIWrapper:

    _logger: logging.Logger = logging.getLogger(__name__)
    _client: OpenAI

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError('OPENAI API key is required.')

        self._api_key = api_key
        self._model = model

        self._client = OpenAI(api_key=self._api_key)
        self._logger.info(f"Client created: {self._client}")
        self._logger.debug(f'api_key: {self._api_key}')

    @property
    def client(self) -> OpenAI:
        return self._client

    @property
    def threads(self):
        return self.client.beta.threads

    @property
    def messages(self):
        return self.client.beta.threads.messages

    def create_assistant(self,
                         name: str,
                         description: str,
                         instructions: str) -> Assistant:
        self._logger.info("Creating assistant")

        assistant = self.client.beta.assistants.create(name=name,
                                                       description=description,
                                                       instructions=instructions,
                                                       model=self._model)
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
        return converters.to_message(message)

    def create_run(self,
                   assistant_id: str,
                   thread_id: str,
                   instructions: str = '') -> Run:
        self._logger.info(f'Creating run in thread {thread_id} '
                          f'in assistant {assistant_id}')
        run = self.threads.runs.create(assistant_id=assistant_id,
                                       thread_id=thread_id,
                                       instructions=instructions)
        self._logger.info(f"Run ID: {run.id}")
        return converters.to_run(run)

    def retrieve_run(self, run_id: str, thread_id: str) -> Run:
        self._logger.info(f'Retrieving run [{run_id}] in thread [{thread_id}]')
        run = self.threads.runs.retrieve(
            run_id=run_id, thread_id=thread_id)
        self._logger.info(f'Run: {run}')
        return converters.to_run(run)

    def get_run_status(self, run_id: str, thread_id: str) -> str:
        run = self.retrieve_run(run_id, thread_id)
        return run['status']

    def _run_info(self, run: OpenAIRun) -> None:
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

    def list_runs(self, thread_id: str) -> list[Run]:
        return [
            converters.to_run(run)
            for run in self.threads.runs.list(thread_id=thread_id)
        ]

    def list_messages(
            self,
            thread: str,
            *,
            after: Optional[str] = None,
            before: Optional[str] = None,
            limit: Optional[int] = None,
            sort: Optional[Literal['asc', 'desc']] = None) -> list[Message]:
        """
        Retrieve a list of messages from a thread.

        Args:
            thread (str): The ID of the thread.

            after (str, optional): A cursor for use in pagination. `after` is an
                object ID that defines your place in the list. For instance, 
                if you make a list request and receive 100 objects, ending with
                obj_foo, your subsequent call can include after=obj_foo in order
                to fetch the next page of the list.

            before (str, optional): A cursor for use in pagination. `before` is an
                object ID that defines your place in the list. For instance, if you
                make a list request and receive 100 objects, ending with obj_foo, your
                subsequent call can include before=obj_foo in order to fetch the
                previous page of the list.

            limit (int, optional): A limit on the number of objects to be returned.
                Limit can range between 1 and 100, and the default is 20.

            sort (Literal["asc", "desc"], optional): Sort order by the `created_at`
                timestamp of the objects. `asc` for ascending order and `desc` 
                (the default) for descending order.

        Returns:
            list[Message]: Messages in the thread.
        """
        list_args: dict[str, str | int] = {'thread_id': thread}
        if after:
            list_args['after'] = after
        if before:
            list_args['before'] = before
        if limit:
            list_args['limit'] = limit
        if sort:
            list_args['order'] = sort

        self._logger.info(f"Retrieving messages [{list_args}]")
        try:
            message_list = self.messages.list(**list_args)  # type: ignore

            print(message_list)

            for message in message_list:
                self._logger.info(message)
            return [converters.to_message(message) for message in message_list]
        except Exception as e:
            self._logger.error(f"Error retrieving messages: {e}")
            return []


def get_openai() -> OpenAIWrapper:
    if 'openai' not in g:
        g.openai = OpenAIWrapper(
            api_key=current_app.config['OPENAI_API_KEY'],  # type: ignore
            model=current_app.config['OPENAI_MODEL'],  # type: ignore
        )

    return g.openai
