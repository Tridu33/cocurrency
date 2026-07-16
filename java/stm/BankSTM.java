/**
 * BankSTM.java
 *
 * Paradigm: STM (Software Transactional Memory) — simulated with fixed-order locks
 *
 * Java has no built-in STM like Haskell's STM monad. This example simulates
 * STM semantics using:
 *   - Fixed-order lock acquisition (no deadlock)
 *   - Optimistic read phase, then lock+validate+commit phase
 *   - Automatic retry on concurrent modification
 *
 * This is a SIMULATION — true STM (like Haskell's) requires runtime support.
 *
 * Compare with: Python stm_model.py, Haskell STMBank.hs
 *
 * Compile:  javac stm/BankSTM.java
 * Run:      cd stm && java BankSTM
 */

import java.util.concurrent.*;
import java.util.concurrent.locks.ReentrantLock;

public class BankSTM {

    // ---- STM-style Account with versioning ----
    static class Account {
        final String id;
        private long balance;
        private long version = 0;
        final ReentrantLock lock = new ReentrantLock();

        Account(String id, long initialBalance) {
            this.id = id;
            this.balance = initialBalance;
        }

        long getBalance() { return balance; }
        void setBalance(long b) { balance = b; }
        long getVersion() { return version; }
        void incVersion() { version++; }
    }

    // ---- Transaction result ----
    static class TransferResult {
        final boolean success;
        final String message;
        TransferResult(boolean success, String message) {
            this.success = success;
            this.message = message;
        }
    }

    /**
     * STM-style transfer with retry on conflict.
     *
     * Phases:
     *   1. Optimistic read — snapshot balances without locking
     *   2. Lock & validate — acquire locks, verify versions haven't changed
     *   3. Commit — apply the transfer atomically
     *   4. Retry — if validation fails, sleep briefly and retry
     *
     * Lock order is always by account id — prevents deadlock.
     */
    static TransferResult transfer(Account from, Account to, long amount)
            throws InterruptedException {
        // Fixed lock order
        Account first, second;
        if (from.id.compareTo(to.id) < 0) { first = from; second = to; }
        else { first = to; second = from; }

        int maxRetries = 100;
        for (int attempt = 0; attempt < maxRetries; attempt++) {
            // Phase 1: Optimistic snapshot (read versions without locking)
            long vFrom, vTo, balFrom, balTo;
            synchronized (first) { vFrom = first.getVersion(); balFrom = first.getBalance(); }
            synchronized (second) { vTo = second.getVersion(); balTo = second.getBalance(); }

            // Determine actual from/to balances
            long actualFrom = (first == from) ? balFrom : balTo;

            if (actualFrom < amount) {
                return new TransferResult(false,
                    "Insufficient funds in " + from.id);
            }

            // Phase 2: Acquire locks and validate versions
            first.lock.lock();
            try {
                second.lock.lock();
                try {
                    // Validate: versions unchanged since our optimistic read?
                    long cvFrom = first.getVersion();
                    long cvTo = second.getVersion();

                    if (cvFrom == vFrom && cvTo == vTo) {
                        // Phase 3: Commit — versions match, transfer safe
                        long fBal = first.getBalance();
                        long sBal = second.getBalance();

                        if (first == from) {
                            first.setBalance(fBal - amount);
                            second.setBalance(sBal + amount);
                        } else {
                            second.setBalance(fBal - amount);
                            first.setBalance(sBal + amount);
                        }
                        first.incVersion();
                        second.incVersion();

                        return new TransferResult(true,
                            "Transferred " + amount + " from " + from.id + " to " + to.id);
                    }
                    // Validation failed → someone else wrote concurrently → retry
                } finally {
                    second.lock.unlock();
                }
            } finally {
                first.lock.unlock();
            }

            // Phase 4: Backoff before retry
            Thread.sleep(ThreadLocalRandom.current().nextInt(1, 3));
        }

        return new TransferResult(false, "Max retries exceeded (too much contention)");
    }

    // ---- Demo ----
    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== STM Simulation: Bank Transfer ===\n");

        Account accA = new Account("Alice", 1000);
        Account accB = new Account("Bob", 500);

        long initialTotal = accA.getBalance() + accB.getBalance();
        System.out.println("Initial: A=" + accA.getBalance() + ", B=" + accB.getBalance()
            + ", total=" + initialTotal);

        // Concurrent transfers
        int numThreads = 8;
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);

        for (int i = 0; i < numThreads; i++) {
            executor.submit(() -> {
                try {
                    TransferResult result = transfer(accA, accB,
                        ThreadLocalRandom.current().nextInt(10, 50));
                    if (!result.success) {
                        System.out.println("  Transfer failed: " + result.message);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
        }

        executor.shutdown();
        if (!executor.awaitTermination(3, TimeUnit.SECONDS)) {
            executor.shutdownNow();
        }

        long finalTotal = accA.getBalance() + accB.getBalance();
        System.out.println("\nFinal: A=" + accA.getBalance() + ", B=" + accB.getBalance()
            + ", total=" + finalTotal);
        System.out.println("Total conserved: " + (finalTotal == initialTotal));

        System.out.println("\n=== Note ===");
        System.out.println("This STM simulation uses version-checking with retry.");
        System.out.println("True STM (like Haskell's) requires runtime support.");
    }
}
