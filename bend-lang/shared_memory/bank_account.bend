# shared_memory/bank_account.bend — Pure functional bank account with state threading
#
# Analogous to: python/shared_memory_lock/bank_account.py
#
# Python uses threading.Lock to protect shared mutable balance.
# Bend is pure functional — there is no shared mutable state. Instead we
# thread account state explicitly through each operation, which guarantees
# atomicity (like acquiring a lock for the duration of one function call).
#
# Transfers use a strategy analogous to fixed-order locking: we process
# operations sequentially through a global ledger state, guaranteeing
# conservation of money without locks.

# ── Account state ──────────────────────────────────────────────────────────

type Account:
  Acc { id_str, balance }

# ── Single operations ──────────────────────────────────────────────────────

def deposit(acc, amount):
  match acc:
    case Account/Acc:
      return Account/Acc { id_str: acc.id_str, balance: acc.balance + amount }

def withdraw(acc, amount):
  match acc:
    case Account/Acc:
      if amount <= acc.balance:
        return Account/Acc { id_str: acc.id_str, balance: acc.balance - amount }
      else:
        return acc  # insufficient funds — no-op

def get_balance(acc):
  match acc:
    case Account/Acc:
      return acc.balance

# ── Transfer with state threading ─────────────────────────────────────────
#
# In Bend, we process a list of operations sequentially.  Because every
# operation is a pure function, there is no interleaving — this is
# equivalent to holding a lock for the entire batch.

def transfer(from_acc, to_acc, amount):
  #Transfer money between two accounts — atomic in one function call.
  match from_acc:
    case Account/Acc:
      match to_acc:
        case Account/Acc:
          if amount > from_acc.balance:
            # Transfer fails — return unchanged
            return (from_acc, to_acc)
          elif amount <= 0:
            # Transfer fails — return unchanged
            return (from_acc, to_acc)
          else:
            new_from = Account/Acc { id_str: from_acc.id_str, balance: from_acc.balance - amount }
            new_to   = Account/Acc { id_str: to_acc.id_str, balance: to_acc.balance + amount }
            return (new_from, new_to)

# ── Multi-threaded simulation ──────────────────────────────────────────────
#
# We simulate concurrent workers by applying a batch of operations.
# Because the operations are pure, they commute: applying them in any
# order yields the same final state.

def batch_deposit(acc, n, amount):
  #Deposit 'amount' n times.
  switch n:
    case 0:
      return acc
    case _:
      new_acc = deposit(acc, amount)
      return batch_deposit(new_acc, n - 1, amount)

def batch_transfers(from_acc, to_acc, n, amount):
  #Perform n random transfers between accounts.
  switch n:
    case 0:
      return (from_acc, to_acc)
    case _:
      pair = transfer(from_acc, to_acc, amount)
      (new_from, new_to) = pair
      return batch_transfers(new_from, new_to, n - 1, amount)

# ── Demo ───────────────────────────────────────────────────────────────────

def demo_single_account:
  #Single account: 5 deposits of 5 = 25.
  acc = Account/Acc { id_str: "ACC-001", balance: 100 }
  acc = batch_deposit(acc, 5, 5)
  return get_balance(acc)  # 100 + 25 = 125

def demo_transfer:
  #Transfer between accounts with conservation check.
  a = Account/Acc { id_str: "A-savings", balance: 500 }
  b = Account/Acc { id_str: "B-checking", balance: 300 }
  (a, b) = transfer(a, b, 100)
  return get_balance(a) + get_balance(b)  # Must be 800

def demo_concurrent_transfers:
  #Simulate 10 concurrent transfers of 10 from A to B.
  a = Account/Acc { id_str: "A-savings", balance: 500 }
  b = Account/Acc { id_str: "B-checking", balance: 300 }
  (a, b) = batch_transfers(a, b, 10, 10)
  return get_balance(a) + get_balance(b)  # Must be 800

def main():
  result1 = demo_single_account        # 125
  result2 = demo_transfer              # 800
  result3 = demo_concurrent_transfers  # 800
  return result1 + result2 + result3   # 1725
