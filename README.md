# Tallkotte

This is an attempt to use OpenAI Assistant to review CVs.

## Running the app

Create a virtual environment and install the requirements:
```sh
python3 -m venv path/to/venv
pip install -r requirements.txt
```

Run the server:

```sh
flask --app src/tallkotte run [--debug] [--port PORT]
```

## Endpoints

### Send a Message

```
POST /message
Content-Type: application/json

{"text": "Summarize the CV of John Doe"}
```

This returns a Message object, as shown below:

```json
{
    "content": [
        "Summarize the CV of John Doe"
    ],
    "created_at": 1711992736,
    "id": "msg_B2GTTdyAxzyC2aeSQJi3P1Xf",
    "role": "user",
    "run_id": "run_ClD5W2INBdLoiYJGBzWmwDhA",
    "thread_id": "thread_uaw30EcQnmQceaXLNaZy9vpT"
}
```

The `id` of the message should be used to make the request to get the response.

### Get Response

```
GET /messages/msg_B2GTTdyAxzyC2aeSQJi3P1Xf/response HTTP/1.1
Host: <host:port>
```

This returns the response to the specified message.

```json
[
    {
        "content": [
            "Shyam Anand's startup experience is not explicitly detailed in the provided resume. The resume highlights roles at established companies like Google, Turvo, and others, but specific startup experience or ventures are not mentioned. Therefore, there is no information available to summarize Shyam's startup experience based on the resume provided."
        ],
        "created_at": 1711992737,
        "id": "msg_jnp9ITGeT59ZhokkVjrNgU4p",
        "role": "assistant",
        "run_id": "run_ClD5W2INBdLoiYJGBzWmwDhA",
        "thread_id": "thread_uaw30EcQnmQceaXLNaZy9vpT"
    }
]
```