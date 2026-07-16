/**
 * BankAccount.java
 *
 * Demonstrates Java thread safety mechanisms for shared-memory concurrency:
 *   1. synchronized methods for mutual exclusion
 *   2. wait() / notifyAll() for producer-consumer coordination
 *   3. Inconsistent lock ordering causing deadlock
 *
 * Compile:  javac shared_memory_lock/BankAccount.java
 * Run:      cd shared_memory_lock && java BankAccount
 */
public class BankAccount {

    /** The account balance — shared mutable state protected by 'this' monitor. */
    private double balance;

    // ---------------------------------------------------------------
    // Thread-safe operations
    // ---------------------------------------------------------------

    public BankAccount(double initialBalance) {
        this.balance = initialBalance;
    }

    /**
     * Deposit funds. Synchronized to prevent races with concurrent
     * deposits or withdrawals.  Notifies any thread that might be
     * waiting for funds (wait/notify producer-consumer pattern).
     */
    public synchronized void deposit(double amount) {
        if (amount > 0) {
            balance += amount;
            System.out.println(Thread.currentThread().getName()
                + " deposited " + amount + ", new balance = " + balance);
            notifyAll();               // wake up any waiting consumer
        }
    }

    /**
     * Withdraw funds.  Blocks (via wait()) if the balance is
     * insufficient — the calling thread releases the monitor and
     * goes to sleep until notified by a depositor.
     */
    public synchronized void withdraw(double amount) throws InterruptedException {
        while (balance < amount) {
            System.out.println(Thread.currentThread().getName()
                + " wants " + amount + " but balance is only " + balance
                + "  => waiting...");
            wait();                    // releases lock, re-acquires on notify
        }
        balance -= amount;
        System.out.println(Thread.currentThread().getName()
            + " withdrew " + amount + ", new balance = " + balance);
    }

    public synchronized double getBalance() {
        return balance;
    }

    // ---------------------------------------------------------------
    // Demonstration 1 — Producer-Consumer with wait/notify
    // ---------------------------------------------------------------
    private static void demonstrateProducerConsumer() throws InterruptedException {
        System.out.println("\n==========================================");
        System.out.println("DEMO 1 : Producer-Consumer (wait / notify)");
        System.out.println("==========================================\n");

        BankAccount account = new BankAccount(0);

        // Producer: deposits 200 five times
        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    account.deposit(200);
                    Thread.sleep(400);       // simulate work between deposits
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Producer");

        // Consumer: withdraws 150 five times (will wait when balance < 150)
        Thread consumer = new Thread(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    account.withdraw(150);
                    Thread.sleep(100);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Consumer");

        producer.start();
        consumer.start();

        producer.join();
        consumer.join();

        System.out.println("\nFinal balance after all transactions: " + account.getBalance());
    }

    // ---------------------------------------------------------------
    // Demonstration 2 — Deadlock from inconsistent lock ordering
    // ---------------------------------------------------------------
    private static void demonstrateDeadlock() throws InterruptedException {
        System.out.println("\n==========================================");
        System.out.println("DEMO 2 : Deadlock (inconsistent lock order)");
        System.out.println("==========================================\n");

        BankAccount accountA = new BankAccount(1000);
        BankAccount accountB = new BankAccount(1000);

        // Thread 1: lock A then B
        Thread t1 = new Thread(() -> {
            try {
                synchronized (accountA) {
                    System.out.println("  [T1] Locked accountA, trying to lock accountB...");
                    Thread.sleep(100);      // give T2 time to lock B
                    synchronized (accountB) {
                        System.out.println("  [T1] Locked accountB — transfer would happen here");
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Deadlock-T1");

        // Thread 2: lock B then A  (OPPOSITE order — this causes deadlock!)
        Thread t2 = new Thread(() -> {
            try {
                synchronized (accountB) {
                    System.out.println("  [T2] Locked accountB, trying to lock accountA...");
                    Thread.sleep(100);      // give T1 time to lock A
                    synchronized (accountA) {
                        System.out.println("  [T2] Locked accountA — transfer would happen here");
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Deadlock-T2");

        // Mark as daemon so the JVM can exit cleanly after detection
        t1.setDaemon(true);
        t2.setDaemon(true);

        t1.start();
        t2.start();

        // Wait long enough for both to grab their first lock and then block
        Thread.sleep(1500);

        System.out.println("\n  Thread states after 1.5 seconds:");
        System.out.println("  " + t1.getName() + " => " + t1.getState());
        System.out.println("  " + t2.getName() + " => " + t2.getState());

        if (t1.getState() == Thread.State.BLOCKED
                && t2.getState() == Thread.State.BLOCKED) {
            System.out.println("\n  *** DEADLOCK DETECTED ***");
            System.out.println("  T1 holds accountA, waits for accountB");
            System.out.println("  T2 holds accountB, waits for accountA");
            System.out.println("  Neither can ever proceed.\n");
            System.out.println("  Fix : always acquire locks in a consistent global order");
            System.out.println("  (e.g., lock the account with the smaller identity first).");
        }

        // JVM exits -> daemon threads are terminated automatically
    }

    // ---------------------------------------------------------------
    // Main entry point
    // ---------------------------------------------------------------
    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== BankAccount : Shared-Memory Lock Demos ===");
        System.out.println("  Java version : " + System.getProperty("java.version"));
        System.out.println("  Processors   : " + Runtime.getRuntime().availableProcessors());

        demonstrateProducerConsumer();
        demonstrateDeadlock();

        System.out.println("\n=== Demo complete (JVM exiting) ===");
    }
}
