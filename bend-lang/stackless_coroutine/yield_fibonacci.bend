# stackless_coroutine/yield_fibonacci.bend — Lazy Fibonacci sequence
#
# Analogous to: python/stackless_coroutine/yield_fibonacci.py
#
# Python uses generator functions with `yield` to produce Fibonacci lazily.
# Bend uses recursion to build lists lazily — the HVM2 runtime evaluates
# only as much of the list as needed (demand-driven reduction).
#
# "Stackless coroutines" in Python keep state on the heap. In Bend,
# all state is on the heap (or rather in the interaction net) — there's
# no call stack in the traditional sense.

# ── Fibonacci sequence ─────────────────────────────────────────────────────

def fib_seq_upto(n):
  #Generate Fibonacci numbers up to n terms — like a generator.
  return fib_aux(n, 0, 1)

def fib_aux(n, a, b):
  #Tail-recursive auxiliary: accumulates the sequence in reverse.
  switch n:
    case 0:
      return []
    case _:
      rest = fib_aux(n - 1, b, a + b)
      return List/Cons { head: a, tail: rest }

def fib_seq_infinite(n):
  #Simulate an infinite Fibonacci stream by generating on demand.
  return fib_aux_infinite(n, 0, 1)

def fib_aux_infinite(n, a, b):
  #Like fib_aux but only generates n values.
  switch n:
    case 0:
      return []
    case _:
      return List/Cons { head: a, tail: fib_aux_infinite(n - 1, b, a + b) }

# ── Lazy evaluation demonstration ──────────────────────────────────────────
#
# Bend is lazy by default — list elements are computed only when consumed.
# We demonstrate this by generating a large sequence but only taking
# a small prefix.

def take(n, xs):
  #Take the first n elements of a list.
  match xs:
    case List/Nil:
      return []
    case List/Cons:
      switch n:
        case 0:
          return []
        case _:
          return List/Cons { head: xs.head, tail: take(n - 1, xs.tail) }

def sum_list(xs):
  #Sum all elements of a list.
  match xs:
    case List/Nil:
      return 0
    case List/Cons:
      return xs.head + sum_list(xs.tail)

# ── Fibonacci pair sequence (like the Python yield_from example) ───────────

def fib_pairs(n):
  #Generate (a, b) Fibonacci pairs for n terms.
  switch n:
    case 0:
      return []
    case _:
      return rec_fib_pairs(n, 0, 1)

def rec_fib_pairs(n, a, b):
  switch n:
    case 0:
      return []
    case _:
      return List/Cons { head: (a, b), tail: rec_fib_pairs(n - 1, b, a + b) }

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_basic:
  #First 10 Fibonacci numbers.
  seq = fib_seq_upto(10)
  return sum_list(seq)  # 0+1+1+2+3+5+8+13+21+34 = 88

def demo_take:
  #Infinite stream, take first 7.
  seq = fib_seq_infinite(7)
  return sum_list(seq)  # 0+1+1+2+3+5+8 = 20

def demo_pairs:
  #Fibonacci pairs (5 terms).
  pairs = fib_pairs(5)
  # Extract first element of first pair to verify
  match pairs:
    case List/Cons:
      (a, b) = pairs.head
      return a + b  # (0, 1) -> 1
    case _:
      return 0

def main():
  r1 = demo_basic   # 88
  r2 = demo_take    # 20
  r3 = demo_pairs   # 1
  return r1 + r2 + r3  # 109
