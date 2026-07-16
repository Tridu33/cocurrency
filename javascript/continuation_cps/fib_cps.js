// =============================================================================
// continuation_cps / fib_cps.js
//
// Concurrency Paradigm: Continuation-Passing Style (CPS)
//
// CPS transforms recursive functions by passing a "continuation" function
// that receives the result instead of returning it directly.  This makes
// control flow explicit and enables features like early exit, non-local
// return, and trampolining.
//
// Compare with: Python continuation_cps.py, Haskell ContMonad
// =============================================================================

// ---------------------------------------------------------------------------
// 1. Direct-style Fibonacci
// ---------------------------------------------------------------------------

function fibDirect(n) {
  if (n <= 1) return n;
  return fibDirect(n - 1) + fibDirect(n - 2);
}

// ---------------------------------------------------------------------------
// 2. CPS Fibonacci
// ---------------------------------------------------------------------------

function fibCps(n, cont) {
  if (n <= 1) return cont(n);
  return fibCps(n - 1, (a) => fibCps(n - 2, (b) => cont(a + b)));
}

// ---------------------------------------------------------------------------
// 3. CPS Factorial
// ---------------------------------------------------------------------------

function factCps(n, cont) {
  if (n === 0) return cont(1);
  return factCps(n - 1, (res) => cont(n * res));
}

// ---------------------------------------------------------------------------
// 4. Trampoline — avoids stack overflow for deep CPS
// ---------------------------------------------------------------------------

class Bounce {
  static call(thunk) {
    return { type: "call", thunk };
  }
  static done(value) {
    return { type: "done", value };
  }
}

function trampoline(b) {
  let result = b;
  while (result.type === "call") {
    result = result.thunk();
  }
  return result.value;
}

function fibCpsTramp(n, cont) {
  if (n <= 1) return cont(n);
  return Bounce.call(() =>
    fibCpsTramp(n - 1, (a) =>
      Bounce.call(() => fibCpsTramp(n - 2, (b) => cont(a + b)))
    )
  );
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

console.log("=== Continuation / CPS Demo ===\n");

// CPS Fibonacci
console.log("--- CPS Fibonacci ---");
for (let n = 0; n <= 10; n++) {
  const direct = fibDirect(n);
  const cps = fibCps(n, (x) => x);
  console.log(`  fib(${n}) = ${direct} (CPS: ${cps})`);
  console.assert(direct === cps, "Mismatch!");
}
console.log();

// CPS Factorial
console.log("--- CPS Factorial ---");
for (let n = 0; n <= 7; n++) {
  const cps = factCps(n, (x) => x);
  console.log(`  fact(${n}) = ${cps}`);
}
console.log();

// Trampoline (deep recursion without stack overflow)
console.log("--- Trampolined CPS ---");
const result = trampoline(fibCpsTramp(20, (x) => Bounce.done(x)));
console.log(`  fib_cps_trampoline(20) = ${result}`);
console.assert(result === fibDirect(20), "Mismatch!");
console.log();

console.log("=== Key insight ===");
console.log("CPS makes control flow explicit by passing continuations.");
console.log("Each recursive call receives a function describing");
console.log("'what to do next' instead of returning a value.");
