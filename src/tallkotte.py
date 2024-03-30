from flask import Flask, request
from .assistant.assistant import AssistantService
from .setup import ASSISTANT_ID

app = Flask(__name__)

cvassistant = AssistantService(ASSISTANT_ID)


@app.route('/')
def home():
    return {
        'status': 'ok'
    }


@app.route('/assistant')
def assistant():
    return {
        'assistant': cvassistant
    }


@app.route('/messages', methods=['POST', 'GET'])  # type: ignore[no-any-return]
def messages():  # type: ignore[no-any-return]
    if request.method == 'POST':
        text = request.args.get('message')
        if not text:
            raise ValueError('No message provided')

        message = cvassistant.send_message(text)
        return (message, 201)
    elif request.method == 'GET':
        run_id = request.args.get('run')
        after = request.args.get('after')
        return {
            'messages': get_messages(run_id, after)  # type: ignore
        }

    return {
        'error': f'Unsupported method {request.method}'
    }
