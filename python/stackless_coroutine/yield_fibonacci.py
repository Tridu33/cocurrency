"""
yield_fibonacci.py — Generator-based (stackless) Fibonacci.

Demonstrates:
  - Python generators as stackless coroutines.
  - yield / yield from for lazy sequence generation.
  - Generator-based coroutine with send() for two-way communication.
"""


def fibonacci_yield(n: int):
    """
    Generate Fibonacci numbers up to n terms using yield.

    This is a classic stackless coroutine: the generator's state
    (local variables a, b, i) is kept on the heap, not on a call stack.
    """
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


def fibonacci_yield_infinite():
    """Generate Fibonacci numbers indefinitely."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def fibonacci_with_send():
    """
    Generator that accepts values via send() to modify behaviour.

    Two-way coroutine: yield produces the next fib number,
    send can reset the sequence to a new starting pair.
    """
    a, b = 0, 1
    while True:
        received = yield a
        if received is not None:
            # Reset to a custom pair
            a, b = received[0], received[1]
        else:
            a, b = b, a + b


def fibonacci_yield_from(n: int):
    """
    Demonstrate yield from by delegating to a sub-generator.

    This produces fibonacci pairs (a, b) for n terms.
    """

    def _pair_gen(m: int):
        a, b = 0, 1
        for _ in range(m):
            yield (a, b)
            a, b = b, a + b

    yield from _pair_gen(n)


def demo_yield_fibonacci() -> None:
    """Demonstrate all generator-based Fibonacci variants."""
    print("=== Stackless Coroutine: Generator Fibonacci ===\n")

    # Basic yield
    print("fibonacci_yield(10):")
    result = list(fibonacci_yield(10))
    print(f"  {result}")
    assert result == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    # Infinite, take 7
    print("\nfibonacci_yield_infinite (first 7):")
    inf_gen = fibonacci_yield_infinite()
    result2 = [next(inf_gen) for _ in range(7)]
    print(f"  {result2}")
    assert result2 == [0, 1, 1, 2, 3, 5, 8]

    # Two-way coroutine with send()
    print("\nfibonacci_with_send (send to reset):")
    coro = fibonacci_with_send()
    vals = [next(coro)]  # start — primes the generator
    for _ in range(5):
        vals.append(coro.send(None))
    print(f"  first 6 fib numbers: {vals}")
    assert vals == [0, 1, 1, 2, 3, 5]

    # Reset via send
    coro.send((10, 20))
    vals2 = [coro.send(None) for _ in range(3)]
    print(f"  after reset to (10, 20): {vals2}")
    assert vals2 == [10, 20, 30]

    # yield from
    print("\nfibonacci_yield_from (5 pairs):")
    result3 = list(fibonacci_yield_from(5))
    print(f"  {result3}")
    assert result3 == [(0, 1), (1, 1), (1, 2), (2, 3), (3, 5)]

    print("\nAll generator Fibonacci demos passed.")


if __name__ == "__main__":
    demo_yield_fibonacci()
