# csp/channel_demo.bend — CSP-style channel communication via streams
#
# Analogous to: python/csp/channel_demo.py
#
# Python's CSP demo uses threads + a Channel class with blocking send/recv.
# Bend is pure functional — there are no blocking operations. Instead we
# model *channel communication* as a stream: a lazy list that producers
# generate and consumers reduce.
#
# Bend's parallelism means the producer and consumer branches can be
# evaluated concurrently by the HVM2 runtime, giving the same logical
# effect as concurrent goroutines over a channel.

# ── Channel as a stream ────────────────────────────────────────────────────
#
# A "channel" is just a list: the producer generates values, and the
# consumer reduces them.  In HVM2, the producer and consumer are both
# reducible expressions that the runtime interleaves automatically,
# analogous to how goroutines communicate over a channel.

def producer(start, count):
  #Generate 'count' values starting from 'start' — like sending on a channel.
  switch count:
    case 0:
      return []
    case _:
      return List/Cons { head: start, tail: producer(start + 1, count - 1) }

def consumer_sum(ch, acc):
  #Consume all values from the channel by summing them.
  match ch:
    case List/Nil:
      return acc
    case List/Cons:
      return consumer_sum(ch.tail, acc + ch.head)

def consumer_collect(ch):
  #Consume all values from the channel — like recv in a loop.
  return ch

# ── Buffered channel simulation ────────────────────────────────────────────
#
# A buffered channel allows the producer to get ahead of the consumer up
# to the buffer size.  In Bend this is just a list — all values exist
# simultaneously, so the "buffer" is the whole stream.

def multi_producer():
  #Simulate multiple producers by merging streams.
  p1 = producer(1, 3)
  p2 = producer(101, 3)
  return append(p1, p2)

def append(xs, ys):
  match xs:
    case List/Nil:
      return ys
    case List/Cons:
      return List/Cons { head: xs.head, tail: append(xs.tail, ys) }

# ── Non-blocking operations ────────────────────────────────────────────────
#
# Since there is no blocking in Bend, "non-blocking" is the default.
# try_send / try_recv become simple list operations.

def try_send(ch, item):
  #Returns (new_channel, True/False) — but in Bend it always succeeds.
  return (append([item], ch), 1)

def try_recv(ch):
  #Returns (item, new_channel, True) or (0, ch, False) if empty.
  match ch:
    case List/Nil:
      return (0, ch, 0)
    case List/Cons:
      return (ch.head, ch.tail, 1)

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_unbuffered:
  #Unbuffered channel: producer sends 3 items, consumer sums them.
  ch = producer(1, 3)
  # In Bend, the consumer runs immediately — the list is already built.
  return consumer_sum(ch, 0)

def demo_buffered:
  #Buffered channel: two producers, their streams concatenated.
  ch = multi_producer()
  return consumer_sum(ch, 0)

def demo_try_ops:
  #Non-blocking operations simulation.
  ch = []
  (ch, ok) = try_send(ch, 42)
  (item, ch, found) = try_recv(ch)
  return item

# ── Main ───────────────────────────────────────────────────────────────────

def main():
  unbuf = demo_unbuffered       # 1 + 2 + 3 = 6
  buf   = demo_buffered         # (1+2+3) + (101+102+103) = 312
  nt    = demo_try_ops          # 42
  return unbuf + buf + nt       # 6 + 312 + 42 = 360
