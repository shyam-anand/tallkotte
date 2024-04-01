from typing import Dict, List, Literal, TypedDict, Union

_Message = Dict[str, Union[str, int, List[str], None]]


class Message(TypedDict):
    id: str
    role: Literal['user', 'assistant']
    created_at: int
    run_id: str
    thread_id: str
    content: list[str]


# Run(
    # id='run_d9feUwv76GEFUIHF9JWacqXY',
    # assistant_id='asst_5idNKSayD7TnxaXyqxgrLHtU',
    # cancelled_at=None,
    # completed_at=1711464229,
    # created_at=1711464221,
    # expires_at=None,
    # failed_at=None,
    # file_ids=[],
    # instructions="You are a CV reviewer.\n  You read CVs, and understand the candidate's skillset, work experience, and \n  other relevant factors. From the CVs, you create summaries, and answer\n  questions about how much the candidate fits certain roles, and why the\n  candidate may be or may not be fit for certain roles. You can also rewrite\n  CVs to align with different roles or job requirements. Your answers will be\n  derived based on the data in the CV, and you are not permitted to add data\n  that is not mentioned in the CV.\n  ",
    # last_error=None,
    # metadata={},
    # model='gpt-3.5-turbo',
    # object='thread.run',
    # required_action=None,
    # started_at=1711464226,
    # status='expired',
    # thread_id='thread_uaw30EcQnmQceaXLNaZy9vpT',
    # tools=[RetrievalTool(type='retrieval')],
    # usage=Usage(
    # completion_tokens=150,
    # prompt_tokens=3876,
    # total_tokens=4026),
    # temperature=1)

class Usage(TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class Run(TypedDict):
    id: str
    created_at: int | None
    started_at: int | None
    completed_at: int | None
    status: str
    thread_id: str
    usage: Usage | None
