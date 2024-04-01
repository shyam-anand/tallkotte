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
POST /messages HTTP/1.1
Host: <host:port>
Content-Type: application/json
Content-Length: 46

{
    "text": "Summarize the CV of John Doe"
}
```

The `id` of the message should be used to make the request to get the response.

### Get Response

```
GET /messages/msg_B2GTTdyAxzyC2aeSQJi3P1Xf/response HTTP/1.1
Host: <host:port>
```