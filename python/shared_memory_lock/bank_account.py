"""
bank_account.py — Shared-memory concurrency with threading.Lock.

Demonstrates:
  - A simple BankAccount protected by a threading.Lock.
  - Fixed-order locking to prevent deadlock when transferring between accounts.
  - Multiple threads performing deposits, withdrawals, and transfers.
"""

import threading
import random


class BankAccount:
    """A thread-safe bank account using a Lock."""

    def __init__(self, account_id: str, initial_balance: int = 0):
        self.account_id = account_id
        self.balance = initial_balance
        self._lock = threading.Lock()

    def deposit(self, amount: int) -> None:
        """Deposit amount into this account."""
        with self._lock:
            if amount <= 0:
                raise ValueError("Deposit amount must be positive")
            self.balance += amount

    def withdraw(self, amount: int) -> None:
        """Withdraw amount from this account."""
        with self._lock:
            if amount <= 0:
                raise ValueError("Withdrawal amount must be positive")
            if amount > self.balance:
                raise ValueError(f"Insufficient funds: balance={self.balance}, withdrawal={amount}")
            self.balance -= amount

    def get_balance(self) -> int:
        """Return current balance."""
        with self._lock:
            return self.balance


def transfer(from_account: BankAccount, to_account: BankAccount, amount: int) -> None:
    """
    Transfer `amount` from `from_account` to `to_account`.
    Uses fixed-order locking on account_id to prevent deadlock.
    """
    # Fixed-order: always lock the account with the smaller id first.
    first, second = sorted([from_account, to_account], key=lambda a: a.account_id)

    with first._lock:
        with second._lock:
            if amount <= 0:
                raise ValueError("Transfer amount must be positive")
            if from_account.balance < amount:
                raise ValueError(
                    f"Insufficient funds in {from_account.account_id}: "
                    f"balance={from_account.balance}, transfer={amount}"
                )
            from_account.balance -= amount
            to_account.balance += amount


def _worker_deposit(account: BankAccount, count: int, results: list) -> None:
    """Deposit random amounts repeatedly."""
    for _ in range(count):
        account.deposit(random.randint(1, 10))


def _worker_transfer(
    accounts: list[BankAccount],
    count: int,
    errors: list,
) -> None:
    """Perform random transfers between accounts."""
    for _ in range(count):
        a, b = random.sample(accounts, 2)
        amount = random.randint(1, 5)
        try:
            transfer(a, b, amount)
        except ValueError as e:
            errors.append(e)


def demo_bank_account() -> None:
    """Run a demo of the bank account with concurrent operations."""
    print("=== BankAccount with Lock Demo ===\n")

    # Single-account operations
    acc = BankAccount("ACC-001", 100)
    print(f"Initial balance: {acc.get_balance()}")

    threads = []
    for _ in range(5):
        t = threading.Thread(target=_worker_deposit, args=(acc, 20, []))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"Final balance after 5 threads x 20 deposits: {acc.get_balance()}")
    # Each deposit is random 1..10, so expected sum ≈ 100 + 5*20*5.5 = 650
    assert 500 <= acc.get_balance() <= 800, f"Unexpected balance: {acc.get_balance()}"
    print()

    # Transfer with fixed-order locking
    acc_a = BankAccount("A-savings", 500)
    acc_b = BankAccount("B-checking", 300)
    print(f"Before transfers: A={acc_a.get_balance()}, B={acc_b.get_balance()}")

    errors: list = []
    transfer_threads = []
    for _ in range(10):
        t = threading.Thread(
            target=_worker_transfer,
            args=([acc_a, acc_b], 30, errors),
        )
        transfer_threads.append(t)
        t.start()

    for t in transfer_threads:
        t.join()

    total = acc_a.get_balance() + acc_b.get_balance()
    print(f"After transfers: A={acc_a.get_balance()}, B={acc_b.get_balance()}")
    print(f"Total (conserved): {total} (should be 800)")
    print(f"Transfer errors (insufficient funds): {len(errors)}")
    assert total == 800, f"Money conservation violated! Total={total}"
    print("OK: money conserved across all concurrent transfers.")


if __name__ == "__main__":
    demo_bank_account()
