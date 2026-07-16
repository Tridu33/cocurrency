"""Tests for stackful_coroutine/greenlet_demo.py."""

from stackful_coroutine.greenlet_demo import demo_greenlet


class TestGreenletDemo:
    def test_demo_runs(self):
        """The demo should complete without error (with or without greenlet)."""
        demo_greenlet()
