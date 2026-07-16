"""Tests for stm/stm_model.py."""

import threading
from stm.stm_model import (
    create_tvar, read_tvar, atomically, retry, TVar,
    stm_bank_transfer, demo_stm,
)


class TestSTM:
    def test_create_and_read(self):
        t = create_tvar(42)
        assert read_tvar(t) == 42

    def test_write_and_read(self):
        t = create_tvar(0)

        def set_and_get(txn):
            txn.write_tvar(t, 100)
            return txn.read_tvar(t)

        result = atomically(set_and_get)
        assert result == 100
        assert read_tvar(t) == 100

    def test_money_conservation(self):
        a = create_tvar(1000)
        b = create_tvar(500)

        def transfer(txn):
            ba = txn.read_tvar(a)
            bb = txn.read_tvar(b)
            txn.write_tvar(a, ba - 200)
            txn.write_tvar(b, bb + 200)
            return "ok"

        atomically(transfer)
        total = read_tvar(a) + read_tvar(b)
        assert total == 1500
        assert read_tvar(a) == 800
        assert read_tvar(b) == 700

    def test_retry_on_insufficient_funds(self):
        """Transfer that succeeds because concurrent deposits fund it."""
        a = create_tvar(10)
        b = create_tvar(500)
        ledger = create_tvar(0)

        # This one should retry (not enough in A) but eventually succeed
        # because another thread deposits into A.
        result = stm_bank_transfer(a, b, 50, ledger)
        assert "OK" in result

    def test_concurrent_transfers(self):
        a = create_tvar(5000)
        b = create_tvar(5000)
        ledger = create_tvar(0)
        n_threads = 10
        ops = 50

        def worker():
            for _ in range(ops):
                stm_bank_transfer(a, b, 1, ledger)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = read_tvar(a) + read_tvar(b)
        assert total == 10000

    def test_demo_runs(self):
        demo_stm()
