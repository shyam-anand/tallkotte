from .assistant.assistant_service import AssistantService
from .setup import ASSISTANT_ID
from .assistant.openai import openai
from flask import Flask, request, jsonify
from markupsafe import escape
import logging
import traceback

app = Flask(__name__)

assistant_service = AssistantService(ASSISTANT_ID)


@app.errorhandler(500)
@app.errorhandler(Exception)
def internal_server_error(e: Exception):
    app.logger.error(e)
    if app.logger.isEnabledFor(logging.DEBUG):
        traceback.print_exc()
    return jsonify(error=str(e)), 500  # type: ignore


@app.route('/')
def home():
    return {
        'status': 'ok'
    }


@app.route('/openai/threads/<thread_id>/messages')
def thread_messages(thread_id: str):
    messages = openai.list_messages(
        thread_id,
        request.args.get('after'),
        request.args.get('before'),
        request.args.get('limit'),  # type: ignore
        request.args.get('sort'))  # type: ignore

    return jsonify(messages)


@app.route('/assistant')
def assistant():
    return jsonify(assistant_service.state)


@app.route('/threads/<thread_id>/messages', methods=['GET'])
def get_messages(thread_id: str):
    after = request.args.get('after')

    messages = assistant_service.get_messages(
        thread_id=escape(thread_id), after=after)
    return jsonify(messages)


@app.route('/messages', methods=['POST'])  # type: ignore[no-any-return]
def messages():  # type: ignore[no-any-return]
    request_json = request.get_json()
    text = request_json['text'] if request_json \
        else request.args.get('message')
    if not text:
        raise ValueError('No message provided')

    message = assistant_service.send_message(text)
    if '_id' in message.keys():
        del message['_id']  # type: ignore
    return message, 201


@app.route('/runs/<run_id>', methods=['GET'])
def run(run_id: str):
    run = assistant_service.get_run(escape(run_id))
    return jsonify(run)


@app.route('/messages/<message_id>/response', methods=['GET'])
def get_response(message_id: str):
    return jsonify(
        assistant_service.get_response(escape(message_id))
    )
