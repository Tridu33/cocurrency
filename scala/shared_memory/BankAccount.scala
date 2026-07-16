/**
 * BankAccount.scala
 *
 * JVM shared-memory concurrency using synchronized blocks.
 * Demonstrates thread-safe operations on a bank account via
 * intrinsic locks (synchronized) and cooperative transfer
 * between accounts.
 */

import scala.collection.mutable

// ---------------------------------------------------------------------------
// Account
// ---------------------------------------------------------------------------

class Account(val id: String, initialBalance: Double) {

  /** Mutable balance — only ever accessed inside synchronized blocks. */
  private var _balance = initialBalance

  /** Snapshot of current balance (thread-safe). */
  def balance: Double = this.synchronized { _balance }

  /** Thread-safe deposit. Returns the new balance. */
  def deposit(amount: Double): Double = this.synchronized {
    if (amount <= 0)
      throw new IllegalArgumentException(s"deposit amount must be positive (got $amount)")
    _balance += amount
    println(s"[Account $id] deposited +$amount → balance = $balance")
    _balance
  }

  /**
   * Thread-safe withdrawal.
   * Throws IllegalArgumentException if funds are insufficient.
   */
  def withdraw(amount: Double): Double = this.synchronized {
    if (amount <= 0)
      throw new IllegalArgumentException(s"withdraw amount must be positive (got $amount)")
    if (amount > _balance)
      throw new IllegalArgumentException(
        s"insufficient funds in account $id: need $amount but have ${_balance}")
    _balance -= amount
    println(s"[Account $id] withdrew -$amount → balance = $balance")
    _balance
  }

  /** Provides a consistent snapshot for reporting. */
  def snapshot: (String, Double) = this.synchronized {
    (id, _balance)
  }
}

// ---------------------------------------------------------------------------
// Transfer logic — demonstrates nested synchronized blocks
// ---------------------------------------------------------------------------

object Transfer {

  /**
   * Transfer `amount` from `from` to `to`.
   *
   * To avoid deadlock we always lock accounts in a global order
   * (by their id string). This is a simple but effective strategy
   * for fine-grained locking.
   */
  def transfer(from: Account, to: Account, amount: Double): Unit = {
    val (first, second) =
      if (from.id < to.id) (from, to) else (to, from)

    first.synchronized {
      second.synchronized {
        if (amount <= 0)
          throw new IllegalArgumentException("transfer amount must be positive")
        if (from.balance < amount)
          throw new IllegalArgumentException(
            s"insufficient funds: account ${from.id} has ${from.balance}, " +
            s"needs $amount for transfer to ${to.id}")

        from.withdraw(amount)
        to.deposit(amount)
        println(s"[Transfer] $amount from ${from.id} → ${to.id} completed")
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Ledger — a shared, thread-safe collection of accounts
// ---------------------------------------------------------------------------

class Ledger {
  private val accounts = mutable.LinkedHashMap.empty[String, Account]

  /** Create a new account (thread-safe). */
  def openAccount(id: String, initialBalance: Double): Account = this.synchronized {
    if (accounts.contains(id))
      throw new IllegalArgumentException(s"account '$id' already exists")
    val acct = new Account(id, initialBalance)
    accounts(id) = acct
    println(s"[Ledger] opened account '$id' with $$$initialBalance")
    acct
  }

  /** Look up an account by id. */
  def getAccount(id: String): Option[Account] = this.synchronized {
    accounts.get(id)
  }

  /** Print a full statement of all accounts (consistent snapshot). */
  def printStatement(): Unit = this.synchronized {
    println("\n=== Bank Statement ===")
    var total = 0.0
    for ((id, acct) <- accounts) {
      val (aid, bal) = acct.snapshot
      total += bal
      println(f"  $aid%-20s $$$bal%.2f")
    }
    println(f"  ${"---"}%-20s ${"---"}%-8s")
    println(f"  ${"Total"}%-20s $$$total%.2f")
    println("=====================\n")
  }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

object BankAccount {

  def main(args: Array[String]): Unit = {
    println("=== Bank Account (Shared Memory + Locks) Demo ===\n")

    val ledger = new Ledger()

    val alice = ledger.openAccount("alice", 1000.0)
    val bob   = ledger.openAccount("bob",   500.0)
    val carol = ledger.openAccount("carol",  250.0)

    ledger.printStatement()

    // --- Single-threaded operations ---
    println("--- Basic operations ---")
    alice.deposit(200.0)
    bob.withdraw(100.0)
    ledger.printStatement()

    // --- Multi-threaded transfers ---
    println("--- Concurrent transfers (8 threads) ---")

    val threads = Seq.newBuilder[Thread]

    // 4 threads transferring from alice to bob
    for (i <- 1 to 4) {
      val idx = i
      val t = new Thread {
        override def run(): Unit = {
          try {
            Transfer.transfer(alice, bob, 50.0)
          } catch {
            case e: IllegalArgumentException =>
              println(s"[Thread $idx] transfer failed: ${e.getMessage}")
          }
        }
      }
      t.setName(s"tx-alice->bob-$i")
      threads += t
    }

    // 4 threads transferring from bob to carol
    for (i <- 1 to 4) {
      val idx = i
      val t = new Thread {
        override def run(): Unit = {
          try {
            Transfer.transfer(bob, carol, 25.0)
          } catch {
            case e: IllegalArgumentException =>
              println(s"[Thread $idx] transfer failed: ${e.getMessage}")
          }
        }
      }
      t.setName(s"tx-bob->carol-$i")
      threads += t
    }

    // Start all threads
    for (t <- threads.result()) { t.start() }
    // Wait for all threads
    for (t <- threads.result()) { t.join() }

    ledger.printStatement()

    // --- Attempt an overdraft ---
    println("--- Overdraft attempt ---")
    try {
      alice.withdraw(999999.0)
    } catch {
      case e: IllegalArgumentException =>
        println(s"  Overdraft blocked: ${e.getMessage}")
    }

    // --- Final state ---
    ledger.printStatement()

    // --- Verify total is preserved ---
    val total = alice.balance + bob.balance + carol.balance
    println(f"Sum of all accounts = $$$total%.2f (should be 1750.00)")
    println("\n=== Bank Account Demo complete ===")
  }
}
