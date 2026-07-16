"""Tests for stackless_coroutine/yield_fibonacci.py."""

from stackless_coroutine.yield_fibonacci import (
    fibonacci_yield,
    fibonacci_yield_infinite,
    fibonacci_with_send,
    fibonacci_yield_from,
    demo_yield_fibonacci,
)


class TestYieldFibonacci:
    def test_fibonacci_yield(self):
        assert list(fibonacci_yield(0)) == []
        assert list(fibonacci_yield(1)) == [0]
        assert list(fibonacci_yield(2)) == [0, 1]
        assert list(fibonacci_yield(10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    def test_fibonacci_yield_infinite(self):
        gen = fibonacci_yield_infinite()
        first_10 = [next(gen) for _ in range(10)]
        assert first_10 == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    def test_fibonacci_with_send(self):
        coro = fibonacci_with_send()
        vals = [next(coro)]  # prime
        for _ in range(5):
            vals.append(coro.send(None))
        assert vals == [0, 1, 1, 2, 3, 5]

        # Reset via send
        coro.send((10, 20))
        vals2 = [coro.send(None) for _ in range(3)]
        assert vals2 == [10, 20, 30]

    def test_fibonacci_yield_from(self):
        result = list(fibonacci_yield_from(5))
        assert result == [(0, 1), (1, 1), (1, 2), (2, 3), (3, 5)]

    def test_demo_runs(self):
        demo_yield_fibonacci()
