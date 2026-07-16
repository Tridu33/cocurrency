"""Tests for stackless_coroutine/stackless_vs_stackful.py."""

from stackless_coroutine.stackless_vs_stackful import (
    run_stackless,
    run_stackful,
    benchmark,
    demo_comparison,
)


class TestStacklessVsStackful:
    def test_identical_output_n0(self):
        assert run_stackless(0) == run_stackful(0)

    def test_identical_output_n3(self):
        assert run_stackless(3) == run_stackful(3)

    def test_identical_output_n5(self):
        assert run_stackless(5) == run_stackful(5)

    def test_identical_output_n10(self):
        sl = run_stackless(10)
        sf = run_stackful(10)
        assert sl == sf
        assert len(sl) == 31  # 1 leaf + 10*3 (enter/exit steps)

    def test_stackless_depth(self):
        result = run_stackless(3)
        assert "enter n=0" in result[0] or "enter n=3" in result[0]
        assert "leaf" in str(result)
        assert "exit n=0" in result[-1] or "exit n=3" in result[-1]

    def test_benchmark_runs(self):
        result = benchmark(50)
        assert result["stackless_steps"] > 0
        assert result["stackful_steps"] > 0
        assert result["stackless_steps"] == result["stackful_steps"]

    def test_demo_runs(self):
        demo_comparison()
