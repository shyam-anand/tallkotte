from .assistant.assistant_service import get_assistant
from flask import Blueprint, current_app, jsonify, request
from markupsafe import escape
import logging
import traceback

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.errorhandler(500)
@bp.errorhandler(Exception)
def internal_server_error(e: Exception):
    current_app.logger.error(e)
    if current_app.logger.isEnabledFor(logging.DEBUG):
        traceback.print_exc()
    return jsonify(error=str(e)), 500  # type: ignore


@bp.route('/')
def home():
    return {
        'status': 'ok'
    }


@bp.route('/openai/threads/<thread_id>/messages')
def thread_messages(thread_id: str):
    messages = get_assistant().get_messages(
        thread_id,
        after=request.args.get('after'),
        before=request.args.get('before'),
        limit=request.args.get('limit'),  # type: ignore
        sort=request.args.get('sort'))  # type: ignore

    return jsonify(messages)


@bp.route('/assistant')
def assistant():
    return get_assistant().state


@bp.route('/threads/<thread_id>/messages', methods=['GET'])
def get_messages(thread_id: str):
    after = request.args.get('after')

    messages = get_assistant().get_messages(
        thread_id=escape(thread_id), after=after)
    return jsonify(messages)


@bp.route('/messages', methods=['POST'])  # type: ignore[no-any-return]
def messages():  # type: ignore[no-any-return]
    request_json = request.get_json()
    text = request_json['text'] if request_json \
        else request.args.get('message')
    if not text:
        raise ValueError('No message provided')

    message = get_assistant().send_message(text)
    if '_id' in message.keys():
        del message['_id']  # type: ignore
    return message, 201


@bp.route('/runs/<run_id>', methods=['GET'])
def run(run_id: str):
    run = get_assistant().get_run(escape(run_id))
    return jsonify(run)


@bp.route('/messages/<message_id>/response', methods=['GET'])
def get_response(message_id: str):
    return jsonify(
        get_assistant().get_response(escape(message_id))
    )
