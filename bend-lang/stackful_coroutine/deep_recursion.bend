# stackful_coroutine/deep_recursion.bend — Deep recursive processing
#
# Analogous to: python/stackful_coroutine/greenlet_demo.py
#             python/stackless_coroutine/stackless_vs_stackful.py
#
# Python uses greenlet (stackful) or generators (stackless) for coroutines.
# Bend has no distinction between stackless and stackful — the HVM2 runtime
# handles all recursion through interaction nets where there is no call
# stack.  Every function call is "stackless" in the sense that it reduces
# to a graph rewrite.
#
# We demonstrate this by running deeply recursive computations that would
# overflow the stack in Python, along with a coroutine-like interleaving
# pattern.

# ── Deep recursion (would overflow Python's stack) ─────────────────────────

def deep_count(n, acc):
  #Count down from n — a deeply recursive computation.
  switch n:
    case 0:
      return acc
    case _:
      return deep_count(n - 1, acc + 1)

def deep_nest(n):
  #Build a deeply nested right-leaning chain, then sum it.
  def build(depth):
    switch depth:
      case 0:
        return 1
      case _:
        return 1 + build(depth - 1)
  return build(n)

# ── Coroutine-style interleaving ──────────────────────────────────────────
#
# Python's greenlet demo shows A->B->C coroutines interleaving steps.
# In Bend, we simulate this by interleaving the steps of three independent
# computations using merge.

def steps_a(n):
  #Coroutine A: process n steps.
  switch n:
    case 0:
      return []
    case _:
      return List/Cons { head: n, tail: steps_a(n - 1) }

def steps_b(n):
  #Coroutine B: process n steps.
  switch n:
    case 0:
      return []
    case _:
      return List/Cons { head: n + 100, tail: steps_b(n - 1) }

def steps_c(n):
  #Coroutine C: process n steps.
  switch n:
    case 0:
      return []
    case _:
      return List/Cons { head: n + 200, tail: steps_c(n - 1) }

def interleave(xs, ys):
  #Interleave two lists — like cooperative scheduling.
  match xs:
    case List/Nil:
      return ys
    case List/Cons:
      return List/Cons { head: xs.head, tail: interleave(ys, xs.tail) }

def schedule(coros):
  #Round-robin scheduler: interleave all coroutine step sequences.
  match coros:
    case List/Nil:
      return []
    case List/Cons:
      return interleave(coros.head, schedule(coros.tail))

# ── Stackless vs stackful comparison ──────────────────────────────────────
#
# Python's stackless_vs_stackful.py compares generator chains (stackless)
# vs explicit stack simulation (stackful).  In Bend, both converge to the
# same representation — recursion through graph reduction.

def chain_enter_exit(n, depth):
  #Generate enter/exit messages for each recursive step — like the Python comparison.
  switch n:
    case 0:
      return [0]  # leaf
    case _:
      return List/Cons { head: n, tail: chain_enter_exit(n - 1, depth + 1) }

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_deep_recursion:
  #Deep recursion without stack overflow.
  d = deep_nest(100)
  return d  # build(100) = 1 + 1 + ... + 1 (101 times, since build(0)=1) = 101

def demo_coroutine_interleaving:
  #Three coroutines interleaved.
  a = steps_a(3)            # [3, 2, 1]
  b = steps_b(3)            # [103, 102, 101]
  c = steps_c(3)            # [203, 202, 201]
  all_steps = [a, b, c]
  scheduled = schedule(all_steps)
  return sum_list(scheduled)

def sum_list(xs):
  match xs:
    case List/Nil:
      return 0
    case List/Cons:
      return xs.head + sum_list(xs.tail)

def demo_chain:
  #Chain enter/exit pattern.
  ch = chain_enter_exit(5, 0)
  return sum_list(ch)

def main():
  r1 = demo_deep_recursion           # 101  (build(100) = 101)
  r2 = demo_coroutine_interleaving   # 3 + 2 + 1 + 103 + 102 + 101 + 203 + 202 + 201 = 918
  r3 = demo_chain                    # 5 + 4 + 3 + 2 + 1 = 15
  return r1 + r2 + r3                # 1034
