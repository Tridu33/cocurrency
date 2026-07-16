"""
stm_model.py — Software Transactional Memory (STM) in pure Python.

Demonstrates:
  - TVar: a versioned transactional variable.
  - atomically(): run a block of code as a single transaction.
  - retry: re-run the transaction when a read condition isn't met.
  - orElse: try one transaction, then another if the first retries.
  - STM vs Lock benchmark comparison.

Inspired by Haskell's STM and Clojure's refs.
"""

import threading
import time
import random


class TVar:
    """
    A transactional variable with versioning.

    Each TVar has a current value and a version counter.
    Transactions track which TVars they read/write so they
    can detect conflicts and retry.
    """

    def __init__(self, value):
        self.value = value
        self.version = 0
        self._lock = threading.Lock()

    def _read(self):
        """Direct read (for internal use, outside transactions)."""
        with self._lock:
            return self.value, self.version

    def _write(self, value):
        """Direct write (for internal use, outside transactions)."""
        with self._lock:
            self.value = value
            self.version += 1


class Transaction:
    """
    Represents an in-progress STM transaction.

    Tracks read-set (for validation) and write-set (for commit).
    """

    def __init__(self):
        self.read_set: dict[int, tuple] = {}  # id -> (value, version)
        self.write_set: dict[int, object] = {}  # id -> new_value
        self._local_cache: dict[int, object] = {}  # id -> value
        self._should_retry = False

    def read_tvar(self, tvar: TVar) -> object:
        """Read a TVar within the transaction."""
        tid = id(tvar)
        if tid in self.write_set:
            return self.write_set[tid]

        with tvar._lock:
            self.read_set[tid] = (tvar.value, tvar.version)
            self._local_cache[tid] = tvar.value
            return tvar.value

    def write_tvar(self, tvar: TVar, value: object) -> None:
        """Write a TVar within the transaction."""
        tid = id(tvar)
        self.write_set[tid] = value
        self._local_cache[tid] = value

    def retry(self) -> None:
        """Signal that the transaction should retry."""
        self._should_retry = True

    @property
    def should_retry(self) -> bool:
        return self._should_retry

    def validate(self) -> bool:
        """Check that all read TVars still have the same version."""
        for tid, (expected_val, expected_ver) in self.read_set.items():
            tvar = _id_to_tvar.get(tid)
            if tvar is None:
                return False
            with tvar._lock:
                if tvar.version != expected_ver:
                    return False
        return True

    def commit(self) -> None:
        """Atomically commit writes if validation passes."""
        if not self.validate():
            raise RuntimeError("Transaction conflict — should retry")

        for tid, new_value in self.write_set.items():
            tvar = _id_to_tvar.get(tid)
            if tvar is not None:
                with tvar._lock:
                    # Re-check version after validation window
                    if tid in self.read_set:
                        _, expected_ver = self.read_set[tid]
                        if tvar.version != expected_ver:
                            raise RuntimeError("Concurrent modification detected")
                    tvar.value = new_value
                    tvar.version += 1


# Global registry: id(TVar) -> TVar (needed for validation/commit)
_id_to_tvar: dict[int, TVar] = {}


def _register(tvar: TVar) -> None:
    _id_to_var[id(tvar)] = tvar


# Thread-local transaction context
_tls = threading.local()
_GLOBAL_LOCK = threading.Lock()


def _get_current_txn() -> Transaction | None:
    """Get the current transaction from thread-local storage, or None."""
    return getattr(_tls, 'current_txn', None)


def atomically(txn_func):
    """
    Execute `txn_func(txn: Transaction)` as a single STM transaction.

    Retries automatically on conflict or when txn.retry() is called.
    """
    while True:
        txn = Transaction()
        old = _get_current_txn()
        _tls.current_txn = txn

        try:
            result = txn_func(txn)
        except RetryException:
            _tls.current_txn = old
            # Wait a bit before retrying
            time.sleep(0.001)
            continue
        finally:
            _tls.current_txn = old

        if txn.should_retry:
            time.sleep(0.001)
            continue

        # Validate and commit
        if txn.validate():
            # Acquire global lock for commit
            with _GLOBAL_LOCK:
                if txn.validate():
                    txn.commit()
                    return result
        # Conflict — retry
        time.sleep(random.uniform(0.001, 0.01))


class RetryException(Exception):
    """Internal exception to signal a retry."""
    pass


def retry() -> None:
    """Inside atomically: abort the current transaction and retry."""
    txn = _get_current_txn()
    if txn is None:
        raise RuntimeError("retry() called outside atomically()")
    txn.retry()
    raise RetryException()


def read_tvar(tvar: TVar) -> object:
    """Read a TVar (works inside or outside a transaction)."""
    txn = _get_current_txn()
    if txn is not None:
        return txn.read_tvar(tvar)
    with tvar._lock:
        return tvar.value


def write_tvar(tvar: TVar, value: object) -> None:
    """Write a TVar inside a transaction."""
    txn = _get_current_txn()
    if txn is None:
        raise RuntimeError("write_tvar() called outside atomically()")
    txn.write_tvar(tvar, value)


def create_tvar(value) -> TVar:
    """Create a new TVar and register it."""
    tvar = TVar(value)
    with _GLOBAL_LOCK:
        _id_to_tvar[id(tvar)] = tvar
    return tvar


# ---------- Application: Bank Transfer ----------

def stm_bank_transfer(from_acc: TVar, to_acc: TVar, amount: int, ledger: TVar) -> None:
    """Transfer money between two STM accounts."""
    def transfer(txn: Transaction) -> str:
        from_bal = txn.read_tvar(from_acc)
        to_bal = txn.read_tvar(to_acc)

        if from_bal < amount:
            txn.retry()
            return ""

        txn.write_tvar(from_acc, from_bal - amount)
        txn.write_tvar(to_acc, to_bal + amount)

        # Update ledger count
        ledger_count = txn.read_tvar(ledger)
        txn.write_tvar(ledger, ledger_count + 1)

        return f"OK: transferred {amount}"
    return atomically(transfer)


# ---------- Benchmark ----------

def benchmark_stm_vs_lock(num_threads: int = 8, ops_per_thread: int = 200) -> dict:
    """
    Compare throughput of STM vs Lock-based bank transfers.

    Returns a dict of results.
    """
    import threading

    print("=== STM vs Lock Benchmark ===\n")

    # --- STM benchmark ---
    acc1_stm = create_tvar(10000)
    acc2_stm = create_tvar(10000)
    ledger_stm = create_tvar(0)

    def stm_worker(count: int):
        for _ in range(count):
            stm_bank_transfer(acc1_stm, acc2_stm, random.randint(1, 10), ledger_stm)

    stm_threads = []
    start = time.perf_counter()
    for _ in range(num_threads):
        t = threading.Thread(target=stm_worker, args=(ops_per_thread,))
        stm_threads.append(t)
        t.start()
    for t in stm_threads:
        t.join()
    stm_time = time.perf_counter() - start

    stm_balance = (read_tvar(acc1_stm) + read_tvar(acc2_stm))
    stm_txns = read_tvar(ledger_stm)

    print(f"  STM:  {num_threads} threads x {ops_per_thread} ops = {stm_txns} transfers")
    print(f"        time={stm_time:.3f}s  total_balance={stm_balance}")
    print(f"        throughput={stm_txns / stm_time:.0f} transfers/s")

    # --- Lock benchmark ---
    lock1 = threading.Lock()
    lock2 = threading.Lock()

    class LockAccount:
        def __init__(self, balance):
            self.balance = balance
            self.lock = threading.Lock()

    la1 = LockAccount(10000)
    la2 = LockAccount(10000)
    lock_transfer_count = 0
    lock_transfer_lock = threading.Lock()

    def lock_worker(count: int):
        nonlocal lock_transfer_count
        for _ in range(count):
            amount = random.randint(1, 10)
            # Fixed-order locking
            first = la1 if id(la1) < id(la2) else la2
            second = la2 if first is la1 else la1
            with first.lock:
                with second.lock:
                    if la1.balance >= amount:
                        la1.balance -= amount
                        la2.balance += amount
                        with lock_transfer_lock:
                            lock_transfer_count += 1

    lock_threads = []
    start = time.perf_counter()
    for _ in range(num_threads):
        t = threading.Thread(target=lock_worker, args=(ops_per_thread,))
        lock_threads.append(t)
        t.start()
    for t in lock_threads:
        t.join()
    lock_time = time.perf_counter() - start

    lock_balance = la1.balance + la2.balance

    print(f"\n  Lock: {num_threads} threads x {ops_per_thread} ops = {lock_transfer_count} transfers")
    print(f"        time={lock_time:.3f}s  total_balance={lock_balance}")
    print(f"        throughput={lock_transfer_count / lock_time:.0f} transfers/s")
    print()

    return {
        "stm_time": stm_time,
        "stm_throughput": stm_txns / stm_time,
        "stm_total_balance": stm_balance,
        "stm_transfers": stm_txns,
        "lock_time": lock_time,
        "lock_throughput": lock_transfer_count / lock_time,
        "lock_total_balance": lock_balance,
        "lock_transfers": lock_transfer_count,
    }


def demo_stm() -> None:
    """Run a demonstration of STM operations."""
    print("=== STM Model Demo ===\n")

    acc_a = create_tvar(1000)
    acc_b = create_tvar(500)
    ledger = create_tvar(0)

    print(f"Initial: A={read_tvar(acc_a)}, B={read_tvar(acc_b)}")

    def transaction1(txn: Transaction) -> str:
        a = txn.read_tvar(acc_a)
        b = txn.read_tvar(acc_b)
        txn.write_tvar(acc_a, a - 100)
        txn.write_tvar(acc_b, b + 100)
        l = txn.read_tvar(ledger)
        txn.write_tvar(ledger, l + 1)
        return f"Transferred 100 from A to B"

    result = atomically(transaction1)
    print(f"After transfer: A={read_tvar(acc_a)}, B={read_tvar(acc_b)}, ledger={read_tvar(ledger)}")
    assert read_tvar(acc_a) == 900
    assert read_tvar(acc_b) == 600
    assert read_tvar(ledger) == 1

    # Concurrent transfers
    threads = []
    for i in range(5):
        t = threading.Thread(
            target=lambda: stm_bank_transfer(acc_a, acc_b, random.randint(10, 50), ledger)
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    total = read_tvar(acc_a) + read_tvar(acc_b)
    print(f"After concurrent transfers: A={read_tvar(acc_a)}, B={read_tvar(acc_b)}")
    print(f"Total (conserved): {total}  Ledger entries: {read_tvar(ledger)}")
    assert total == 1500, f"Money conservation violated! total={total}"
    print("OK: money conserved.")

    # --- orElse demo ---
    print("\n--- orElse demo ---")
    acc_x = create_tvar(10)
    acc_y = create_tvar(1000)
    # Try to transfer 500 from x (fails), falls back to transferring from y
    def try_x(txn: Transaction):
        bal = txn.read_tvar(acc_x)
        if bal >= 500:
            txn.write_tvar(acc_x, bal - 500)
            return "took from X"
        txn.retry()

    def try_y(txn: Transaction):
        bal = txn.read_tvar(acc_y)
        txn.write_tvar(acc_y, bal - 500)
        return f"took from Y (balance was {bal})"

    result = atomically(lambda t: _or_else(t, try_x, try_y))
    print(f"orElse result: {result}")
    print(f"X={read_tvar(acc_x)}, Y={read_tvar(acc_y)}")


def _or_else(txn: Transaction, first, second):
    """
    Try `first`; if it calls retry, fall through to `second`.
    This is a simplified orElse — it captures the retry and runs second.
    """
    # We simulate orElse by wrapping first to catch retry
    original_retry = txn.should_retry

    # Save read-set
    saved_reads = dict(txn.read_set)
    saved_writes = dict(txn.write_set)

    try:
        return first(txn)
    except (RetryException, Exception):
        # Restore state and try second
        txn.read_set.clear()
        txn.read_set.update(saved_reads)
        txn.write_set.clear()
        txn.write_set.update(saved_writes)
        # Clear the retry flag
        txn._should_retry = False
        return second(txn)


if __name__ == "__main__":
    demo_stm()
    print()
    benchmark_stm_vs_lock()
