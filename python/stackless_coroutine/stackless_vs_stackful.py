"""
stackless_vs_stackful.py — Compare stackless and stackful coroutine approaches.

Demonstrates:
  - Stackless: Python generators / asyncio (state on heap).
  - Stackful: greenlet-based or simulated stackful coroutines (separate stack).
  - How each approach handles deep recursion, nested calls, and suspension.
"""

import sys
import time

# ---------- Stackless: Python generators (state on heap) ----------

def stackless_chain(n: int, depth: int = 0):
    """
    A chain of generators that yield values.
    Each generator yields from the next, creating a 'stack' of generator frames
    stored on the heap rather than the call stack.
    """
    if n == 0:
        yield f"leaf at depth={depth}"
    else:
        yield f"enter n={n} depth={depth}"
        yield from stackless_chain(n - 1, depth + 1)
        yield f"exit n={n} depth={depth}"


def run_stackless(max_n: int) -> list[str]:
    """Run a stackless chain of generators."""
    sys.setrecursionlimit(10000)
    result = list(stackless_chain(max_n))
    return result


# ---------- Stackful: Simulated with explicit stack ----------

class StackfulCoroutine:
    """
    Simulate a stackful coroutine using an explicit Python list as a 'stack'.

    Each frame is a dict with:
      - 'n': current n value
      - 'depth': current depth
      - 'phase': where in the execution we are
      - 'sub_result': result from a child frame
    """

    def __init__(self, n: int):
        self.stack = [{'n': n, 'depth': 0, 'phase': 'enter', 'sub_result': None}]
        self.results = []
        self.done = False

    def step(self) -> bool:
        """Execute one step of the stackful coroutine. Returns True if still running."""
        if not self.stack:
            self.done = True
            return False

        frame = self.stack[-1]

        if frame['phase'] == 'enter':
            self.results.append(f"enter n={frame['n']} depth={frame['depth']}")
            if frame['n'] == 0:
                self.results.append(f"leaf at depth={frame['depth']}")
                frame['phase'] = 'exit'
            else:
                # Push child frame
                self.stack.append({
                    'n': frame['n'] - 1,
                    'depth': frame['depth'] + 1,
                    'phase': 'enter',
                    'sub_result': None,
                })
                frame['phase'] = 'after_child'
            return True

        elif frame['phase'] == 'after_child':
            # Child just finished and was popped
            frame['phase'] = 'exit'

        elif frame['phase'] == 'exit':
            self.results.append(f"exit n={frame['n']} depth={frame['depth']}")
            self.stack.pop()
            return True

        return True


def run_stackful(n: int) -> list[str]:
    """Run the stackful simulation to completion."""
    coro = StackfulCoroutine(n)
    while not coro.done:
        coro.step()
    return coro.results


# ---------- Benchmark ----------

def benchmark(n: int = 500) -> dict:
    """Compare performance of stackless vs stackful approaches."""
    print(f"=== Benchmark: stackless vs stackful (n={n}) ===\n")

    # Stackless
    start = time.perf_counter()
    result_stackless = run_stackless(n)
    stackless_time = time.perf_counter() - start

    # Stackful
    start = time.perf_counter()
    result_stackful = run_stackful(n)
    stackful_time = time.perf_counter() - start

    print(f"Stackless: {len(result_stackless)} steps in {stackless_time:.4f}s")
    print(f"Stackful:  {len(result_stackful)} steps in {stackful_time:.4f}s")

    # Verify identical output
    assert result_stackless == result_stackful, "Results differ!"
    print("OK: both produce identical output.")

    return {
        "n": n,
        "stackless_time": stackless_time,
        "stackless_steps": len(result_stackless),
        "stackful_time": stackful_time,
        "stackful_steps": len(result_stackful),
    }


def demo_comparison() -> None:
    """Run the comparison demo."""
    print("=== Stackless vs Stackful Coroutine Comparison ===\n")

    print("Conceptual difference:")
    print("  Stackless: generator frames live on the heap.")
    print("    - `yield from` chains create heap-allocated frame objects.")
    print("    - Lightweight; no separate call stack per coroutine.")
    print("  Stackful: each coroutine has its own call stack.")
    print("    - Can suspend at any call depth without special syntax.")
    print("    - More memory per coroutine; faster resumption.")
    print()

    # Small test
    print("--- Output comparison (n=3) ---")
    sl = run_stackless(3)
    sf = run_stackful(3)
    print(f"Stackless: {sl}")
    print(f"Stackful:  {sf}")
    assert sl == sf
    print()

    # Slightly deeper chain
    print("--- Output comparison (n=5) ---")
    sl5 = run_stackless(5)
    sf5 = run_stackful(5)
    assert sl5 == sf5
    print(f"Steps: {len(sl5)} (identical)")
    print()

    benchmark(200)


if __name__ == "__main__":
    demo_comparison()
