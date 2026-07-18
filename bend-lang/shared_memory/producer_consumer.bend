# shared_memory/producer_consumer.bend — Producer-consumer via functional streams
#
# Analogous to: python/shared_memory_lock/thread_producer_consumer.py
#
# Python uses threading.Condition + a mutable bounded buffer.
# Bend uses pure functions: the producer generates a stream (list) of items,
# the consumer reduces it.  The "buffer" is just the list spine, and HVM2's
# lazy evaluation interleaves producer and consumer automatically.
#
# This is analogous to CSP or the actor model — data flows through a
# pipeline of pure transformations.

# ── Bounded buffer simulation ──────────────────────────────────────────────
#
# A "bounded buffer" of maxsize N is simply a list that we enforce to be
# at most N elements.  In pure Bend, the producer builds the list and the
# consumer traverses it — there is no back-pressure because evaluation is
# demand-driven.

def produce_range(start, count):
  #Produce 'count' items starting from 'start'.
  switch count:
    case 0:
      return []
    case _:
      return List/Cons { head: start, tail: produce_range(start + 1, count - 1) }

def consume_all(buf, acc):
  #Consume all items from the buffer.
  match buf:
    case List/Nil:
      return acc
    case List/Cons:
      return consume_all(buf.tail, acc + buf.head)

# ── Multi-producer / multi-consumer simulation ────────────────────────────
#
# Multiple producers merge their streams via concatenation.
# Multiple consumers split the stream (here one consumer reads all).

def merge_producers(p1, p2):
  #Merge two producer streams — interleave values.
  match p1:
    case List/Nil:
      return p2
    case List/Cons:
      return List/Cons { head: p1.head, tail: merge_producers(p2, p1.tail) }

def append(xs, ys):
  match xs:
    case List/Nil:
      return ys
    case List/Cons:
      return List/Cons { head: xs.head, tail: append(xs.tail, ys) }

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_simple_producer_consumer:
  #One producer, one consumer — produce 10 items, consume them all.
  buf = produce_range(1, 10)
  return consume_all(buf, 0)  # Sum of 1..10 = 55

def demo_two_producers:
  #Two producers, one consumer — concatenated streams.
  p1 = produce_range(1, 10)        # 1..10
  p2 = produce_range(101, 10)      # 101..110
  combined = append(p1, p2)
  return consume_all(combined, 0)  # (1+...+10) + (101+...+110) = 55 + 1055 = 1110

def demo_two_producers_merged:
  #Two producers interleaved via merge.
  p1 = produce_range(1, 4)        # [1, 2, 3, 4]
  p2 = produce_range(101, 4)      # [101, 102, 103, 104]
  merged = merge_producers(p1, p2)
  return consume_all(merged, 0)

def main():
  r1 = demo_simple_producer_consumer        # 55
  r2 = demo_two_producers                   # 1110
  r3 = demo_two_producers_merged            # 1 + 101 + 2 + 102 + 3 + 103 + 4 + 104 = 420
  return r1 + r2 + r3                       # 1585
