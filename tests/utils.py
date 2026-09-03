import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


async def run_concurrently(
    num_tasks: int,
    task_factory: Callable[[], Awaitable[T]],
) -> list[T]:

    ready_count = 0
    ready_event = asyncio.Event()
    start_event = asyncio.Event()

    async def wrapped_task() -> T:
        nonlocal ready_count
        ready_count += 1
        if ready_count == num_tasks:
            ready_event.set()

        await start_event.wait()
        return await task_factory()

    tasks = [asyncio.create_task(wrapped_task()) for _ in range(num_tasks)]

    await ready_event.wait()
    start_event.set()

    return await asyncio.gather(*tasks)
