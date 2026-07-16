"""Tests for t9_combinations.py."""

from t9_combinations import (
    letter_combinations_recursive,
    letter_combinations_backtrack,
    letter_combinations_generator,
    letter_combinations_cps,
    letter_combinations_cps_chain,
    demo_t9,
)


class TestT9Combinations:
    """Test all four T9 approaches produce identical results."""

    def _assert_all_equal(self, digits, expected=None):
        r1 = letter_combinations_recursive(digits)
        r2 = letter_combinations_backtrack(digits)
        r3 = letter_combinations_generator(digits)
        r4 = letter_combinations_cps(digits)
        r5 = letter_combinations_cps_chain(digits)
        assert r1 == r2 == r3 == r4 == r5
        if expected is not None:
            assert r1 == expected

    def test_empty(self):
        self._assert_all_equal("", [])

    def test_single_digit(self):
        self._assert_all_equal("2", ["a", "b", "c"])

    def test_two_digits(self):
        self._assert_all_equal("23", [
            "ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"
        ])

    def test_three_digits(self):
        result = letter_combinations_recursive("234")
        assert len(result) == 27  # 3 * 3 * 3

    def test_four_digits(self):
        result = letter_combinations_generator("79")
        assert len(result) == 16  # 4 * 4

    def test_with_7_and_9(self):
        self._assert_all_equal("7", ["p", "q", "r", "s"])
        self._assert_all_equal("9", ["w", "x", "y", "z"])

    def test_recursive_specific(self):
        assert letter_combinations_recursive("2") == ["a", "b", "c"]
        assert letter_combinations_recursive("") == []

    def test_backtrack_specific(self):
        assert letter_combinations_backtrack("3") == ["d", "e", "f"]
        assert letter_combinations_backtrack("") == []

    def test_generator_specific(self):
        assert letter_combinations_generator("4") == ["g", "h", "i"]

    def test_demo_runs(self):
        demo_t9()
