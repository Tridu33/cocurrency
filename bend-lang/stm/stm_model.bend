# stm/stm_model.bend — Software Transactional Memory in pure functional style
#
# Analogous to: python/stm/stm_model.py
#
# Python implements STM with versioned TVars, optimistic concurrency, and
# retry loops — all on top of threading.Lock.
#
# Bend is pure functional: there are no locks, no versions, and no retry
# because there is no mutation to conflict over.  Instead, "transactions"
# are pure functions that take a state and return a new state and result.
# The STM concepts map as follows:
#
#   TVar          → explicit state threaded through pure functions
#   atomically()  → a function that takes and returns state
#   retry()       → conditional branching (if insufficient funds, no-op)
#   orElse()      → fallback: try one operation, if it fails try another
#   ledger        → a counter threaded alongside account state
#
# Money conservation is guaranteed by construction (no mutation means no
# inconsistent intermediate states).

# ── State types ────────────────────────────────────────────────────────────

type BankState:
  Bank { acc_a, acc_b, ledger }

type TransferResult:
  Success { msg }
  Insufficient { }

# ── Operations ────────────────────────────────────────────────────────────

def read_balance_a(state):
  match state:
    case BankState/Bank:
      return state.acc_a

def read_balance_b(state):
  match state:
    case BankState/Bank:
      return state.acc_b

def read_ledger(state):
  match state:
    case BankState/Bank:
      return state.ledger

# ── Bank transfer as a "transaction" ──────────────────────────────────────
#
# This is the STM equivalent: it takes a state, checks conditions,
# and returns (new_state, result).  Because there's no shared mutation,
# there's no conflict — the "transaction" either succeeds or fails
# atomically by returning the original state.

def transfer(from_a, to_b, amount, state):
  # Transfer 'amount' from acc_a to acc_b.
  # Returns (new_state, result).  If insufficient funds, returns
  # original state and Insufficient.
  match state:
    case BankState/Bank:
      if state.acc_a >= amount:
        new_state = BankState/Bank {
          acc_a: state.acc_a - amount,
          acc_b: state.acc_b + amount,
          ledger: state.ledger + 1
        }
        return (new_state, TransferResult/Success { msg: "" })
      else:
        return (state, TransferResult/Insufficient {})

# ── Concurrent transfer simulation ─────────────────────────────────────────
#
# We simulate concurrent threads by applying a batch of transfers.
# Because each operation is pure, the order doesn't matter for the
# final total.

def batch_transfer(state, n, amount):
  #Perform n transfers sequentially — simulates concurrent workers.
  switch n:
    case 0:
      return state
    case _:
      pair = transfer(1, 0, amount, state)
      (new_state, result) = pair
      return batch_transfer(new_state, n - 1, amount)

# ── orElse simulation ─────────────────────────────────────────────────────
#
# Try account A first; if insufficient, fall back to account B.

def or_else(amount, state):
  # Try A first, fall back to B.
  # Returns (new_state, msg_or_null).
  result_a = try_transfer_a(amount, state)
  (state_after_a, outcome_a) = result_a
  match outcome_a:
    case TransferResult/Success:
      return (state_after_a, "took from A")
    case TransferResult/Insufficient:
      result_b = try_transfer_b(amount, state_after_a)
      (state_after_b, outcome_b) = result_b
      match outcome_b:
        case TransferResult/Success:
          return (state_after_b, "took from B")
        case TransferResult/Insufficient:
          return (state_after_b, "")

def try_transfer_a(amount, state):
  #Try transferring from acc_a.
  match state:
    case BankState/Bank:
      if state.acc_a >= amount:
        new_state = BankState/Bank {
          acc_a: state.acc_a - amount,
          acc_b: state.acc_b + amount,
          ledger: state.ledger + 1
        }
        return (new_state, TransferResult/Success { msg: "took from A" })
      else:
        return (state, TransferResult/Insufficient {})

def try_transfer_b(amount, state):
  #Try transferring from acc_b (source becomes b).
  match state:
    case BankState/Bank:
      if state.acc_b >= amount:
        new_state = BankState/Bank {
          acc_a: state.acc_a + amount,
          acc_b: state.acc_b - amount,
          ledger: state.ledger + 1
        }
        return (new_state, TransferResult/Success { msg: "took from B" })
      else:
        return (state, TransferResult/Insufficient {})

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_basic_transfer:
  #Basic transfer: A=1000, B=500, transfer 100 from A to B.
  init = BankState/Bank { acc_a: 1000, acc_b: 500, ledger: 0 }
  pair = transfer(1, 0, 100, init)
  (final, result) = pair
  match final:
    case BankState/Bank:
      return final.acc_a + final.acc_b  # Must be 1500

def demo_conservation:
  #Concurrent transfers: money must be conserved.
  init = BankState/Bank { acc_a: 10000, acc_b: 10000, ledger: 0 }
  final = batch_transfer(init, 50, 10)
  match final:
    case BankState/Bank:
      return final.acc_a + final.acc_b  # Must be 20000

def demo_or_else:
  #orElse: try X (insufficient), fallback to Y.
  init = BankState/Bank { acc_a: 10, acc_b: 1000, ledger: 0 }
  pair = or_else(500, init)
  (final, msg) = pair
  match final:
    case BankState/Bank:
      return final.acc_a + final.acc_b  # Must be 1010 (10+1000 conserved)

def main():
  r1 = demo_basic_transfer     # 1500
  r2 = demo_conservation       # 20000
  r3 = demo_or_else            # 1010
  return r1 + r2 + r3          # 22510
