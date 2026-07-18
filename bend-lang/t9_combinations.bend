# t9_combinations.bend — T9 keypad letter combinations
#
# Analogous to: python/t9_combinations.py
#
# Python shows 4 approaches: recursive, backtracking, generator, CPS.
# Bend uses pure functional recursion — the most natural fit for the
# language.  Because Bend is functional, the recursive and CPS approaches
# are essentially the same: recursion with explicit continuations.

# ── Keypad mapping ─────────────────────────────────────────────────────────
#
# T9 mapping: 2->abc, 3->def, 4->ghi, 5->jkl, 6->mno, 7->pqrs, 8->tuv, 9->wxyz

type Digits:
  D2 {}
  D3 {}
  D4 {}
  D5 {}
  D6 {}
  D7 {}
  D8 {}
  D9 {}

def letters(d):
  match d:
    case Digits/D2:
      return ["a", "b", "c"]
    case Digits/D3:
      return ["d", "e", "f"]
    case Digits/D4:
      return ["g", "h", "i"]
    case Digits/D5:
      return ["j", "k", "l"]
    case Digits/D6:
      return ["m", "n", "o"]
    case Digits/D7:
      return ["p", "q", "r", "s"]
    case Digits/D8:
      return ["t", "u", "v"]
    case Digits/D9:
      return ["w", "x", "y", "z"]

# ── 1. Recursive (divide and conquer) ─────────────────────────────────────

def combinations_rec(digits):
  #Recursive: combine first digit's letters with the rest.
  #(Uses a helper that returns [""] at the leaf so combine works correctly.)
  match digits:
    case List/Nil:
      return []
    case List/Cons:
      return combine_many(letters(digits.head), comb_rec(digits.tail))

def comb_rec(digits):
  #Helper: same as combinations_rec but returns [""] for empty input.
  match digits:
    case List/Nil:
      return [""]
    case List/Cons:
      return combine_many(letters(digits.head), comb_rec(digits.tail))

def combine_many(prefixes, suffixes):
  #Cartesian product: combine each prefix with each suffix.
  match prefixes:
    case List/Nil:
      return []
    case List/Cons:
      return append(map_prepend(prefixes.head, suffixes), combine_many(prefixes.tail, suffixes))

def map_prepend(p, xs):
  #Prepend p to each element of xs.
  match xs:
    case List/Nil:
      return []
    case List/Cons:
      return List/Cons { head: p + xs.head, tail: map_prepend(p, xs.tail) }

def append(xs, ys):
  match xs:
    case List/Nil:
      return ys
    case List/Cons:
      return List/Cons { head: xs.head, tail: append(xs.tail, ys) }

# ── 2. Backtracking (DFS with accumulator) ─────────────────────────────────

def combinations_backtrack(digits):
  #Backtracking: build combinations incrementally.
  return bt_aux(digits, "")

def bt_aux(digits, path):
  match digits:
    case List/Nil:
      return [path]
    case List/Cons:
      return expand_letters(letters(digits.head), digits.tail, path)

def expand_letters(ls, remaining, path):
  #For each letter, recursively build the combination.
  match ls:
    case List/Nil:
      return []
    case List/Cons:
      rest = bt_aux(remaining, path + ls.head)
      return append(rest, expand_letters(ls.tail, remaining, path))

# ── 3. CPS (Continuation-Passing Style) ────────────────────────────────────

def combinations_cps(digits, cont):
  #CPS: pass combinations to a continuation.
  match digits:
    case List/Nil:
      return cont([""])
    case List/Cons:
      return combinations_cps(digits.tail, lambda suffixes: combine_cps(letters(digits.head), suffixes, cont))

def combine_cps(prefixes, suffixes, cont):
  #Combine prefixes and suffixes in CPS.
  match prefixes:
    case List/Nil:
      return cont([])
    case List/Cons:
      return combine_cps(prefixes.tail, suffixes, lambda rest: cont(append(map_prepend(prefixes.head, suffixes), rest)))

# ── Helper: list length ────────────────────────────────────────────────────

def list_len(xs):
  match xs:
    case List/Nil:
      return 0
    case List/Cons:
      return 1 + list_len(xs.tail)

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_recursive:
  #Test recursive with '23'.
  dig = [Digits/D2 {}, Digits/D3 {}]
  result = combinations_rec(dig)
  return list_len(result)  # '23' -> 3 * 3 = 9 combinations

def demo_backtrack:
  #Test backtracking with '2'.
  dig = [Digits/D2 {}]
  result = combinations_backtrack(dig)
  return list_len(result)  # '2' -> 3 combinations

def demo_cps:
  #Test CPS with '7' (pqrs).
  dig = [Digits/D7 {}]
  result = combinations_cps(dig, lambda x: x)
  return list_len(result)  # '7' -> 4 combinations

def demo_empty:
  #Test empty input.
  result = combinations_rec([])
  return list_len(result)  # [] -> 0 combinations

def main():
  r1 = demo_recursive    # 9
  r2 = demo_backtrack    # 3
  r3 = demo_cps          # 4
  r4 = demo_empty        # 0
  return r1 + r2 + r3 + r4  # 16
