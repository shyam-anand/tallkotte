#! /usr/bin/env python3

from .mongo_wrapper import MongoDB
from ..assistant.openai.openai_wrapper import Message
from datetime import datetime
from typing import Any


def _to_message(document: dict[str, Any]) -> Message:
    del document['_id']
    return document


def get_last_message(mongo: MongoDB, thread_id: str) -> Message | None:
    results = mongo.find(
        'messages',
        filter={'thread_id': thread_id},
        sort={'timestamp': -1}
    )

    if len(results) >= 1:
        return _to_message(results[0])

    return None


def main():
    mongo = MongoDB()
    last_message = get_last_message(mongo, 'thread_uaw30EcQnmQceaXLNaZy9vpT')
    if last_message:
      print(type(last_message))
      print(datetime.fromtimestamp(last_message['created_at']))
    else:
      print('No messages')


if __name__ == '__main__':
    main()
