"""
continuation_cps.py — Continuation-Passing Style (CPS) and call/cc emulation.

Demonstrates:
  - CPS transformation: converting direct-style functions to CPS.
  - Closure-based continuation capturing.
  - call/cc (call-with-current-continuation) emulation.
  - Trampoline for safe recursive CPS execution.
"""

import sys
from typing import Callable, Any

# A continuation is a function that accepts a value and continues computation.
Cont = Callable[[Any], Any]


# ======================================================================
# 1. CPS Transformation: Fibonacci
# ======================================================================

def fib_direct(n: int) -> int:
    """Direct-style Fibonacci (recursive)."""
    if n <= 1:
        return n
    return fib_direct(n - 1) + fib_direct(n - 2)


def fib_cps(n: int, cont: Cont) -> Any:
    """
    Fibonacci in Continuation-Passing Style.

    Instead of returning a value, each call passes its result to `cont`.
    """
    if n <= 1:
        return cont(n)
    return fib_cps(n - 1, lambda a: fib_cps(n - 2, lambda b: cont(a + b)))


# ======================================================================
# 2. CPS Transformation: Factorial
# ======================================================================

def fact_direct(n: int) -> int:
    """Direct-style factorial."""
    if n == 0:
        return 1
    return n * fact_direct(n - 1)


def fact_cps(n: int, cont: Cont) -> Any:
    """Factorial in CPS."""
    if n == 0:
        return cont(1)
    return fact_cps(n - 1, lambda res: cont(n * res))


# ======================================================================
# 3. Tail-Recursive CPS with Trampoline
# ======================================================================

class Bounce:
    """
    Represents a thunk (zero-argument function) for the trampoline.
    A Bounce means "keep computing."
    """
    def __init__(self, thunk: Callable):
        self.thunk = thunk


class Done:
    """A Done means 'here is the final value.'"""
    def __init__(self, value):
        self.value = value


def trampoline(bouncy) -> Any:
    """
    Execute a trampolined computation.

    Repeatedly calls thunks until a Done is returned.
    This avoids stack growth for deeply recursive CPS functions.
    """
    result = bouncy
    while isinstance(result, Bounce):
        result = result.thunk()
    return result.value  # Done


def fact_cps_trampoline(n: int, cont: Cont):
    """
    Factorial in CPS with explicit thunk returns for trampolining.
    Each step returns a Bounce to avoid stack growth.
    """
    if n == 0:
        return cont(1)
    # Return a thunk instead of recursing directly
    return Bounce(lambda: fact_cps_trampoline(n - 1, lambda res: cont(n * res)))


def fib_cps_trampoline(n: int, cont: Cont):
    """
    Fibonacci in CPS with trampolining.
    """
    if n <= 1:
        return cont(n)
    return Bounce(
        lambda: fib_cps_trampoline(
            n - 1,
            lambda a: Bounce(
                lambda: fib_cps_trampoline(
                    n - 2,
                    lambda b: cont(a + b)
                )
            )
        )
    )


# ======================================================================
# 4. call/cc — Call-With-Current-Continuation
# ======================================================================

class Continuation:
    """
    Captured continuation — represents "the rest of the computation."
    When invoked with a value, it passes that value to the captured
    continuation.
    """

    def __init__(self, fn: Cont):
        self._fn = fn

    def invoke(self, value: Any) -> Any:
        """Apply this continuation with a value."""
        return self._fn(value)


_global_k: list[Continuation | None] = [None]


def call_cc(fn: Callable[[Continuation], Any]) -> Any:
    """
    Emulate call-with-current-continuation.

    Captures the current continuation (the rest of the program) and
    passes it to `fn`. If `fn` invokes the continuation, execution
    jumps back to the point of call_cc with the given value.

    NOTE: True call/cc requires deep VM support. This is a limited
    simulation using closures and exceptions for non-local control flow.
    """
    class Jump(Exception):
        """Exception used to simulate continuation jumps."""
        def __init__(self, value):
            self.value = value

    def cc(value):
        """Invoke the captured continuation."""
        raise Jump(value)

    try:
        # Wrap the call so 'return' from fn triggers the continuation
        # with the return value.
        result = fn(Continuation(cc))
        return result
    except Jump as j:
        return j.value


def call_cc_example() -> None:
    """Demonstrate call/cc with a simple example: early exit from a loop."""

    print("--- call/cc: early exit example ---")

    # Search for the first even number; if found, return it immediately.
    def search(nums: list[int]) -> int:
        # Capture the continuation that represents "return from search"
        return call_cc(lambda exit_cont: _search_impl(nums, 0, exit_cont))

    def _search_impl(nums: list[int], idx: int, exit_cont: Continuation):
        if idx >= len(nums):
            return -1  # not found
        if nums[idx] % 2 == 0:
            # Found an even number — jump out with this value
            return exit_cont.invoke(nums[idx])
        return _search_impl(nums, idx + 1, exit_cont)

    nums = [1, 3, 5, 7, 8, 9, 11]
    found = search(nums)
    print(f"  First even in {nums}: {found}")
    assert found == 8

    # No even
    nums2 = [1, 3, 5, 7]
    found2 = search(nums2)
    print(f"  First even in {nums2}: {found2}")
    assert found2 == -1


# ======================================================================
# 5. CPS-based Tree Traversal
# ======================================================================

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def tree_walk_cps(node: Node | None, cont: Cont) -> Any:
    """
    In-order tree traversal in CPS.

    Each step receives a continuation that describes what to do next.
    """
    if node is None:
        return cont([])
    return tree_walk_cps(
        node.left,
        lambda left_vals: tree_walk_cps(
            node.right,
            lambda right_vals: cont(left_vals + [node.value] + right_vals),
        ),
    )


# ======================================================================
# Demo
# ======================================================================

def demo_continuation_cps() -> None:
    """Run all continuation/CPS demos."""
    print("=== Continuation / CPS Demo ===\n")

    # 1. CPS Fibonacci
    print("--- CPS Fibonacci ---")
    for n in range(10):
        direct = fib_direct(n)
        cps_result = fib_cps(n, lambda x: x)
        print(f"  fib({n}) = {direct} (CPS: {cps_result})")
        assert direct == cps_result
    print()

    # 2. CPS Factorial
    print("--- CPS Factorial ---")
    for n in range(7):
        direct = fact_direct(n)
        cps_result = fact_cps(n, lambda x: x)
        print(f"  fact({n}) = {direct} (CPS: {cps_result})")
        assert direct == cps_result
    print()

    # 3. Trampolined CPS (deep recursion without stack overflow)
    print("--- Trampolined CPS ---")
    # Regular CPS would blow the stack for large n, but trampoline avoids that
    result = trampoline(fact_cps_trampoline(1000, lambda x: Done(x)))
    print(f"  fact_cps_trampoline(1000) -> {result} (len={len(str(result))})")
    print(f"  (matches direct: {fact_direct(1000) == result})")
    assert fact_direct(1000) == result
    print()

    result_fib = trampoline(fib_cps_trampoline(20, lambda x: Done(x)))
    print(f"  fib_cps_trampoline(20) -> {result_fib}")
    assert result_fib == fib_direct(20)
    print()

    # 4. call/cc
    call_cc_example()
    print()

    # 5. Tree traversal in CPS
    print("--- CPS Tree Traversal ---")
    tree = Node(
        1,
        Node(2, Node(4), Node(5)),
        Node(3, Node(6), Node(7)),
    )
    tree_vals = tree_walk_cps(tree, lambda x: x)
    print(f"  In-order: {tree_vals}")
    assert tree_vals == [4, 2, 5, 1, 6, 3, 7]
    print()

    print("All continuation/CPS demos passed.")


if __name__ == "__main__":
    demo_continuation_cps()
