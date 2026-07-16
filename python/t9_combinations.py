"""
t9_combinations.py — Four solutions for T9 keypad letter combinations.

LeetCode 17. Letter Combinations of a Phone Number.

Demonstrates:
  1. Recursive (divide-and-conquer)
  2. Backtracking (DFS with explicit state)
  3. Generator (yield / yield from)
  4. CPS (Continuation-Passing Style)

All produce the same output for a given digits string.
"""

from typing import List

# T9 keypad mapping
KEY_MAP: dict[str, str] = {
    '2': 'abc',
    '3': 'def',
    '4': 'ghi',
    '5': 'jkl',
    '6': 'mno',
    '7': 'pqrs',
    '8': 'tuv',
    '9': 'wxyz',
}


# ---------- 1. Recursive (divide-and-conquer) ----------

def letter_combinations_recursive(digits: str) -> List[str]:
    """
    Recursive solution.

    Base case: empty digits -> empty list (or [''] for intermediate).
    Recursive: combine first digit's letters with results of the rest.
    """
    if not digits:
        return []

    def _combine(prefix: str, remaining: str) -> List[str]:
        if not remaining:
            return [prefix]

        results = []
        for letter in KEY_MAP[remaining[0]]:
            results.extend(_combine(prefix + letter, remaining[1:]))
        return results

    return _combine('', digits)


# ---------- 2. Backtracking (DFS with explicit state) ----------

def letter_combinations_backtrack(digits: str) -> List[str]:
    """
    Backtracking solution.

    Build combinations incrementally, backtracking when a path is complete.
    """
    if not digits:
        return []

    results: List[str] = []

    def backtrack(path: List[str], idx: int) -> None:
        if idx == len(digits):
            results.append(''.join(path))
            return

        for letter in KEY_MAP[digits[idx]]:
            path.append(letter)
            backtrack(path, idx + 1)
            path.pop()  # backtrack

    backtrack([], 0)
    return results


# ---------- 3. Generator (yield / yield from) ----------

def letter_combinations_generator(digits: str) -> List[str]:
    """
    Generator-based solution using yield from.

    The generator acts as a stackless coroutine, yielding results lazily.
    """
    if not digits:
        return []

    def _gen(prefix: str, remaining: str):
        if not remaining:
            yield prefix
            return
        for letter in KEY_MAP[remaining[0]]:
            yield from _gen(prefix + letter, remaining[1:])

    return list(_gen('', digits))


# ---------- 4. CPS (Continuation-Passing Style) ----------

def letter_combinations_cps(digits: str) -> List[str]:
    """
    CPS solution.

    Instead of returning results, each call passes accumulated combinations
    to a continuation function. The final continuation collects results.
    """
    if not digits:
        return []

    results: List[str] = []

    def cps(prefix: str, remaining: str, cont) -> None:
        if not remaining:
            cont([prefix])
            return

        def inner(letter: str):
            def next_cont(combs):
                cont(combs)
            return lambda combs_from_child: (
                cps(prefix + letter, remaining[1:], lambda combs: next_cont(combs))
                if False
                else None
            )

        # Simplified: accumulate all combinations for the first letter's branch
        all_results: List[str] = []
        for letter in KEY_MAP[remaining[0]]:
            cps(prefix + letter, remaining[1:], lambda combs: all_results.extend(combs))
        cont(all_results)

    cps('', digits, lambda combs: results.extend(combs))
    return results


# ---------- 5. CPS with explicit continuation chain ----------

def letter_combinations_cps_chain(digits: str) -> List[str]:
    """
    CPS with an explicit continuation chain.

    Builds a chain of continuations and evaluates them.
    """
    if not digits:
        return []

    # A continuation that appends to results
    def make_final_cont(results: List[str]):
        def final_cont(combination: str) -> None:
            results.append(combination)
        return final_cont

    # Build the continuation chain
    results: List[str] = []
    cont = make_final_cont(results)

    # Each level wraps the continuation
    for digit in reversed(digits):
        def make_level(d: str, next_cont):
            def level_cont(prefix: str) -> None:
                for letter in KEY_MAP[d]:
                    next_cont(prefix + letter)
            return level_cont
        cont = make_level(digit, cont)

    # Start with empty prefix
    cont('')
    return results


# ---------- Demo ----------

def demo_t9() -> None:
    """Demonstrate all four T9 approaches."""
    print("=== T9 Keypad Combinations (LeetCode 17) ===\n")

    test_cases = ["", "2", "23", "234"]

    for digits in test_cases:
        print(f"--- digits='{digits}' ---")

        r1 = letter_combinations_recursive(digits)
        r2 = letter_combinations_backtrack(digits)
        r3 = letter_combinations_generator(digits)
        r4 = letter_combinations_cps(digits)
        r5 = letter_combinations_cps_chain(digits)

        print(f"  recursive:  {r1}")
        print(f"  backtrack:  {r2}")
        print(f"  generator:  {r3}")
        print(f"  CPS:        {r4}")
        print(f"  CPS chain:  {r5}")

        assert r1 == r2 == r3 == r4 == r5, f"Results differ! {r1} {r2} {r3} {r4} {r5}"
        print("  OK: all match")
        print()

    # Verify known values
    assert letter_combinations_recursive("23") == [
        "ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"
    ]
    assert letter_combinations_generator("2") == ["a", "b", "c"]
    assert letter_combinations_backtrack("") == []
    print("All T9 checks passed.")


if __name__ == "__main__":
    demo_t9()
