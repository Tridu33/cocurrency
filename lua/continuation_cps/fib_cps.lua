--[[
  fib_cps.lua
  Continuation-Passing Style (CPS) Fibonacci.

  Instead of returning values, each function calls a continuation
  function with the result. This makes control flow explicit.
  Compare with: Python continuation_cps.py, Haskell ContMonad
]]

-- Direct-style Fibonacci
local function fib_direct(n)
  if n <= 1 then return n end
  return fib_direct(n - 1) + fib_direct(n - 2)
end

-- CPS Fibonacci
local function fib_cps(n, cont)
  if n <= 1 then
    return cont(n)
  end
  return fib_cps(n - 1, function(a)
    return fib_cps(n - 2, function(b)
      return cont(a + b)
    end)
  end)
end

-- CPS Factorial
local function fact_cps(n, cont)
  if n == 0 then
    return cont(1)
  end
  return fact_cps(n - 1, function(res)
    return cont(n * res)
  end)
end

-- Tail-Recursive Trampoline (avoids stack overflow)
local Trampoline = {}
Trampoline.__index = Trampoline

function Trampoline.call(thunk)
  return setmetatable({ type = "call", thunk = thunk }, Trampoline)
end

function Trampoline.done(value)
  return setmetatable({ type = "done", value = value }, Trampoline)
end

function trampoline(b)
  local result = b
  while result.type == "call" do
    result = result.thunk()
  end
  return result.value
end

local function fib_cps_tramp(n, cont)
  if n <= 1 then
    return cont(n)
  end
  return Trampoline.call(function()
    return fib_cps_tramp(n - 1, function(a)
      return Trampoline.call(function()
        return fib_cps_tramp(n - 2, function(b)
          return cont(a + b)
        end)
      end)
    end)
  end)
end

-- Demo
print("=== Continuation / CPS Demo (Lua) ===\n")

-- CPS Fibonacci
print("--- CPS Fibonacci ---")
for n = 0, 10 do
  local direct = fib_direct(n)
  local cps = fib_cps(n, function(x) return x end)
  print(string.format("  fib(%d) = %d (CPS: %d)", n, direct, cps))
  assert(direct == cps)
end
print()

-- CPS Factorial
print("--- CPS Factorial ---")
for n = 0, 7 do
  local cps = fact_cps(n, function(x) return x end)
  print(string.format("  fact(%d) = %d", n, cps))
end
print()

-- Trampoline
print("--- Trampolined CPS ---")
local result = trampoline(fib_cps_tramp(20, function(x) return Trampoline.done(x) end))
print(string.format("  fib_cps_trampoline(20) = %d", result))
print(string.format("  matches direct: %s", tostring(result == fib_direct(20))))
print()

print("Key insight: CPS makes control flow explicit.")
print("Each function takes a continuation describing 'what to do next'.")
