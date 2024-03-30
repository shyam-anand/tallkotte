from typing import List, Dict, Union

_Message = Dict[str, Union[str, int, List[str], None]]


class Message:
    _id: str
    _role: str
    _created_at: int
    _run_id: str
    _thread_id: str
    _content: list[str]

    def __init__(self, id: str, role: str, created_at: int,
                 run_id: str, thread_id: str, content: list[str]) -> None:
        self._id = id
        self._role = role
        self._created_at = created_at
        self._run_id = run_id
        self._thread_id = thread_id
        self._content = content

    @property
    def id(self) -> str:
      return self._id
    
    @property
    def run_id(self) -> str:
      return self._run_id
    
    @run_id.setter
    def run_id(self, run_id: str) -> None:
      self._run_id = run_id