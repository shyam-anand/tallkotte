from typing import Dict, List, Literal, TypedDict, Union

_Message = Dict[str, Union[str, int, List[str], None]]


class Message(TypedDict):
    id: str
    role: Literal['user', 'assistant']
    created_at: int
    run_id: str
    thread_id: str
    content: list[str]
