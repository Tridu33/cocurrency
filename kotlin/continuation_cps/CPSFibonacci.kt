/**
 * CPSFibonacci.kt
 *
 * Paradigm: Continuation-Passing Style (CPS)
 *
 * Manual CPS transformation of Fibonacci. Each function takes an
 * extra continuation parameter (a function to call with the result)
 * instead of returning the result directly.
 *
 * Compare with: Python continuation_cps.py, Haskell ContMonad
 *
 * Compile: kotlinc -d out continuation_cps/CPSFibonacci.kt
 * Run:     java -cp /usr/share/java/kotlin-stdlib.jar:out CPSFibonacciKt
 */

// ---------------------------------------------------------------
// Direct-style Fibonacci
// ---------------------------------------------------------------
fun fibDirect(n: Long): Long {
    return if (n <= 1) n else fibDirect(n - 1) + fibDirect(n - 2)
}

// ---------------------------------------------------------------
// CPS Fibonacci
// ---------------------------------------------------------------
fun fibCps(n: Long, cont: (Long) -> Long): Long {
    return if (n <= 1) {
        cont(n)
    } else {
        fibCps(n - 1) { a ->
            fibCps(n - 2) { b ->
                cont(a + b)
            }
        }
    }
}

// ---------------------------------------------------------------
// CPS Factorial
// ---------------------------------------------------------------
fun factCps(n: Long, cont: (Long) -> Long): Long {
    return if (n == 0L) {
        cont(1)
    } else {
        factCps(n - 1) { res -> cont(n * res) }
    }
}

// ---------------------------------------------------------------
// Trampoline — avoids stack overflow for deep CPS recursion
// ---------------------------------------------------------------
sealed class Bounce<out T>
class Call<T>(val thunk: () -> Bounce<T>) : Bounce<T>()
class Done<T>(val value: T) : Bounce<T>()

fun <T> trampoline(b: Bounce<T>): T {
    var result = b
    while (result is Call) {
        result = result.thunk()
    }
    return (result as Done).value
}

fun fibCpsTramp(n: Long, cont: (Long) -> Bounce<Long>): Bounce<Long> {
    return if (n <= 1) {
        cont(n)
    } else {
        Call {
            fibCpsTramp(n - 1) { a ->
                Call {
                    fibCpsTramp(n - 2) { b ->
                        cont(a + b)
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------
// Main
// ---------------------------------------------------------------
fun main(args: Array<String>) {
    println("=== Continuation / CPS Demo ===\n")

    // CPS Fibonacci
    println("--- CPS Fibonacci ---")
    for (n in 0L..10L) {
        val direct = fibDirect(n)
        val cps = fibCps(n) { it }
        println("  fib($n) = $direct (CPS: $cps)")
        check(direct == cps) { "Mismatch at n=$n" }
    }
    println()

    // CPS Factorial
    println("--- CPS Factorial ---")
    for (n in 0L..7L) {
        val cps = factCps(n) { it }
        println("  fact($n) = $cps")
    }
    println()

    // Trampolined CPS (deep recursion without stack overflow)
    println("--- Trampolined CPS ---")
    val result = trampoline(fibCpsTramp(20) { Done(it) })
    println("  fib_cps_trampoline(20) = $result")
    check(result == fibDirect(20)) { "Mismatch in trampoline" }
    println()

    println("=== Key insight ===")
    println("CPS transforms recursive calls into continuation chains.")
    println("Each call receives a function describing 'what to do next'.")
}
