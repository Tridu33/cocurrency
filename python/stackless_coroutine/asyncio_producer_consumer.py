"""
asyncio_producer_consumer.py — Asyncio event-loop producer-consumer.

Demonstrates:
  - async/await coroutines (PEP 492) on an asyncio event loop.
  - asyncio.Queue for coroutine-safe communication.
  - Multiple producers and consumers in the same event loop.
  - Graceful shutdown with cancellation.
"""

import asyncio
import random


async def producer(
    queue: asyncio.Queue,
    items: list,
    name: str,
) -> None:
    """Produce items into the asyncio queue."""
    for item in items:
        await asyncio.sleep(random.uniform(0.01, 0.05))
        await queue.put(item)
        print(f"  [{name}] produced {item}  (qsize={queue.qsize()})")
    print(f"  [{name}] done")


async def consumer(
    queue: asyncio.Queue,
    count: int,
    name: str,
    results: list,
) -> None:
    """Consume items from the asyncio queue."""
    for _ in range(count):
        item = await queue.get()
        results.append(item)
        await asyncio.sleep(random.uniform(0.02, 0.06))
        print(f"  [{name}] consumed {item}  (qsize={queue.qsize()})")
        queue.task_done()
    print(f"  [{name}] done")


async def producer_consumer_demo() -> None:
    """Run the asyncio producer-consumer demo."""
    print("--- Asyncio Producer-Consumer ---")

    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=5)

    # Two producers, two consumers
    items1 = list(range(1, 11))
    items2 = list(range(101, 111))
    results: list = []

    producers = [
        producer(queue, items1, "P1"),
        producer(queue, items2, "P2"),
    ]
    consumers = [
        consumer(queue, 10, "C1", results),
        consumer(queue, 10, "C2", results),
    ]

    await asyncio.gather(*producers, *consumers)
    results.sort()
    expected = sorted(items1 + items2)
    print(f"\nAll items: {results}")
    assert results == expected, f"Mismatch: {results} != {expected}"
    print("OK: all produced items consumed exactly once.")


async def worker_coroutine(name: str, delay: float, count: int) -> list[int]:
    """A simple coroutine that does some async work."""
    results = []
    for i in range(count):
        await asyncio.sleep(delay)
        results.append(i)
        print(f"  [{name}] step {i}")
    return results


async def asyncio_demo() -> None:
    """Main demo for asyncio features."""
    print("=== Stackless Coroutine: Asyncio Demo ===\n")

    # Basic coroutines
    print("--- Multiple worker coroutines ---")
    tasks = [
        worker_coroutine("A", 0.03, 4),
        worker_coroutine("B", 0.04, 3),
        worker_coroutine("C", 0.02, 5),
    ]
    gathered = await asyncio.gather(*tasks)
    print(f"Gathered results: {gathered}")
    assert gathered == [[0, 1, 2, 3], [0, 1, 2], [0, 1, 2, 3, 4]]

    print()

    # Producer-consumer
    await producer_consumer_demo()

    print("\nAll asyncio demos passed.")


def main() -> None:
    asyncio.run(asyncio_demo())


if __name__ == "__main__":
    main()
