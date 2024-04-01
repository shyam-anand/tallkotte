from .datatypes import Message, Run, Usage
from openai.types.beta.threads import Run as ThreadRun
from openai.types.beta.threads.message import Message as ThreadMessage
from openai.types.beta.threads.run import Usage as ThreadUsage
from openai.types.beta.threads.text_content_block import TextContentBlock
from typing import Optional

import logging


def to_message(message: ThreadMessage) -> Message:
    message_content: list[str] = []
    for content in message.content:
        if isinstance(content, TextContentBlock):
            message_content.append(content.text.value)
        else:
            logging.warning(f'Unknown content type: {type(content)} {content}')
    return {
        'id': message.id,
        'role': message.role,
        'created_at': message.created_at,
        'run_id': '',
        'thread_id': message.thread_id,
        'content': message_content
    }


def to_usage(usage: Optional[ThreadUsage]) -> Usage | None:
    if not usage:
        return None
    return {
        'completion_tokens': usage.completion_tokens,
        'prompt_tokens': usage.prompt_tokens,
        'total_tokens': usage.total_tokens
    }


def to_run(run: ThreadRun) -> Run:
    return {
        'id': run.id,
        'created_at': run.created_at,
        'started_at': run.started_at,
        'completed_at': run.completed_at,
        'status': run.status,
        'thread_id': run.thread_id,
        'usage': to_usage(run.usage)
    }
