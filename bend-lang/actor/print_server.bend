# actor/print_server.bend — Actor-like message dispatch using ADTs
#
# Analogous to: python/actor/print_server.py
#
# Bend doesn't have threads, mutable mailboxes, or side effects. Instead we
# model the actor pattern's essence: typed ADT messages dispatched by a
# handler, state threaded through a recursive processing loop.
#
# Key: Python's actor uses threads + Queue; Bend's is pure — messages are
# processed by a tail-recursive function that threads an explicit counter
# through.  Bend achieves parallelism when independent branches of the
# computation are evaluated concurrently by the HVM2 runtime.

# ── Message types ──────────────────────────────────────────────────────────

type Msg:
  PrintJob { text }
  Shutdown {}

# ── Server state ───────────────────────────────────────────────────────────

type ServerState:
  St { count }

# ── Single message handler ─────────────────────────────────────────────────

def handle(job, state):
  match job:
    case Msg/PrintJob:
      match state:
        case ServerState/St:
          return ServerState/St { count: state.count + 1 }
    case Msg/Shutdown:
      return state

# ── Process a list — state flows through the loop ──────────────────────────

def process_all(msgs, state):
  match msgs:
    case List/Nil:
      return state
    case List/Cons:
      new_state = handle(msgs.head, state)
      return process_all(msgs.tail, new_state)

# ── Convenience API ────────────────────────────────────────────────────────

def tell(state, text):
  return handle(Msg/PrintJob { text: text }, state)

def shutdown(state):
  return handle(Msg/Shutdown {}, state)

# ── Demo ───────────────────────────────────────────────────────────────────

def demo:
  msgs = [
    Msg/PrintJob { text: "Hello, World!" },
    Msg/PrintJob { text: "Printing document #1" },
    Msg/PrintJob { text: "Printing document #2" },
    Msg/PrintJob { text: "Urgent report" },
    Msg/PrintJob { text: "Final document" },
    Msg/Shutdown {},
  ]
  init = ServerState/St { count: 0 }
  final = process_all(msgs, init)
  match final:
    case ServerState/St:
      return final.count

def main():
  return demo()
