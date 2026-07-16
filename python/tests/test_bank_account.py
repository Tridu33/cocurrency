"""Tests for shared_memory_lock/bank_account.py."""

import pytest
import threading
from shared_memory_lock.bank_account import BankAccount, transfer, demo_bank_account


class TestBankAccount:
    def test_deposit_and_withdraw(self):
        acc = BankAccount("test", 100)
        assert acc.get_balance() == 100
        acc.deposit(50)
        assert acc.get_balance() == 150
        acc.withdraw(30)
        assert acc.get_balance() == 120

    def test_deposit_negative_raises(self):
        acc = BankAccount("test", 100)
        with pytest.raises(ValueError, match="positive"):
            acc.deposit(-10)

    def test_withdraw_negative_raises(self):
        acc = BankAccount("test", 100)
        with pytest.raises(ValueError, match="positive"):
            acc.withdraw(-5)

    def test_withdraw_insufficient_raises(self):
        acc = BankAccount("test", 50)
        with pytest.raises(ValueError, match="Insufficient"):
            acc.withdraw(100)

    def test_transfer_positive_amount(self):
        a = BankAccount("A", 200)
        b = BankAccount("B", 100)
        transfer(a, b, 50)
        assert a.get_balance() == 150
        assert b.get_balance() == 150

    def test_transfer_insufficient_raises(self):
        a = BankAccount("A", 10)
        b = BankAccount("B", 100)
        with pytest.raises(ValueError, match="Insufficient"):
            transfer(a, b, 50)

    def test_concurrent_deposits(self):
        acc = BankAccount("concurrent", 0)
        n_threads = 10
        ops_per_thread = 100

        def worker():
            for _ in range(ops_per_thread):
                acc.deposit(1)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert acc.get_balance() == n_threads * ops_per_thread

    def test_concurrent_transfers_conserve_money(self):
        a = BankAccount("A", 1000)
        b = BankAccount("B", 1000)
        n_threads = 20
        ops = 50

        def worker():
            for _ in range(ops):
                try:
                    transfer(a, b, 1)
                except ValueError:
                    pass

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = a.get_balance() + b.get_balance()
        assert total == 2000

    def test_demo_runs(self):
        demo_bank_account()
