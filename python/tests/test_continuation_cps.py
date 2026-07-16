"""Tests for continuation_cps/continuation_cps.py."""

from continuation_cps.continuation_cps import (
    fib_direct,
    fib_cps,
    fact_direct,
    fact_cps,
    trampoline,
    fact_cps_trampoline,
    fib_cps_trampoline,
    Done,
    call_cc,
    Continuation,
    tree_walk_cps,
    Node,
    demo_continuation_cps,
)


class TestCPS:
    def test_fib_cps_matches_direct(self):
        for n in range(15):
            assert fib_cps(n, lambda x: x) == fib_direct(n)

    def test_fact_cps_matches_direct(self):
        for n in range(10):
            assert fact_cps(n, lambda x: x) == fact_direct(n)

    def test_trampoline_fact(self):
        result = trampoline(fact_cps_trampoline(100, lambda x: Done(x)))
        assert result == fact_direct(100)

    def test_trampoline_fib(self):
        result = trampoline(fib_cps_trampoline(20, lambda x: Done(x)))
        assert result == fib_direct(20)

    def test_trampoline_deep_recursion(self):
        """Trampoline should handle deep recursion without stack overflow."""
        result = trampoline(fact_cps_trampoline(2000, lambda x: Done(x)))
        assert result == fact_direct(2000)

    def test_call_cc_early_exit(self):
        def search(nums):
            return call_cc(lambda exit_cont: _search(nums, 0, exit_cont))

        def _search(nums, idx, exit_cont):
            if idx >= len(nums):
                return -1
            if nums[idx] % 2 == 0:
                return exit_cont.invoke(nums[idx])
            return _search(nums, idx + 1, exit_cont)

        assert search([1, 3, 5, 7, 8, 9]) == 8
        assert search([1, 3, 5, 7]) == -1

    def test_tree_walk_cps(self):
        tree = Node(4,
                    Node(2, Node(1), Node(3)),
                    Node(6, Node(5), Node(7)))
        result = tree_walk_cps(tree, lambda x: x)
        assert result == [1, 2, 3, 4, 5, 6, 7]

    def test_tree_walk_cps_empty(self):
        result = tree_walk_cps(None, lambda x: x)
        assert result == []

    def test_demo_runs(self):
        demo_continuation_cps()
