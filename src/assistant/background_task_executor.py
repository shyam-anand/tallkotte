from typing import Any, Callable
import concurrent.futures

MAX_WORKERS = 5


_executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)


def execute_concurrently(
        func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    _executor.submit(func, *args, **kwargs)
