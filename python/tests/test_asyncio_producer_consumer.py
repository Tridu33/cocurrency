"""Tests for stackless_coroutine/asyncio_producer_consumer.py."""

import asyncio
import pytest
from stackless_coroutine.asyncio_producer_consumer import (
    producer, consumer, worker_coroutine, asyncio_demo,
)


@pytest.mark.asyncio
async def test_worker_coroutine():
    results = await worker_coroutine("test", 0.001, 5)
    assert results == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_producer_consumer():
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=3)
    items = [1, 2, 3, 4, 5]
    results: list = []

    prod = asyncio.create_task(producer(queue, items, "P"))
    cons = asyncio.create_task(consumer(queue, 5, "C", results))

    await asyncio.gather(prod, cons)
    results.sort()
    assert results == items


@pytest.mark.asyncio
async def test_multiple_producers_consumers():
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=5)
    items1 = list(range(1, 6))
    items2 = list(range(101, 106))
    results: list = []

    prods = [
        asyncio.create_task(producer(queue, items1, "P1")),
        asyncio.create_task(producer(queue, items2, "P2")),
    ]
    cons = [
        asyncio.create_task(consumer(queue, 5, "C1", results)),
        asyncio.create_task(consumer(queue, 5, "C2", results)),
    ]

    await asyncio.gather(*prods, *cons)
    results.sort()
    assert results == sorted(items1 + items2)


@pytest.mark.asyncio
async def test_demo_runs():
    await asyncio_demo()
