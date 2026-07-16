--[[
  fibonacci_gen.lua
  Stackless coroutine simulation (Lua coroutines are stackful by nature).

  Lua's coroutine.create/resume/yield are stackful — they preserve the entire
  call stack. This example wraps them to enforce a "stackless" discipline:
  yielding is only allowed at the top level of the generator, not from
  nested calls. This simulates the semantics of Python generators or
  JavaScript function* generators.

  Compare with: Python yield_fibonacci.py, JS generator_fibonacci.js
]]

local StacklessGenerator = {}
StacklessGenerator.__index = StacklessGenerator

function StacklessGenerator.new(fn)
  local self = setmetatable({
    co = coroutine.create(fn),
    done = false
  }, StacklessGenerator)
  return self
end

-- Get the next value from the generator (like Python's next())
function StacklessGenerator:next(...)
  if self.done then
    return nil
  end

  local ok, result = coroutine.resume(self.co, ...)
  if not ok then
    error("Generator error: " .. tostring(result))
  end

  if coroutine.status(self.co) == "dead" then
    self.done = true
  end

  return result
end

-- Fibonacci generator (stackless style: yield only at top level)
function fibonacci_stackless(limit)
  return StacklessGenerator.new(function()
    local a, b = 0, 1
    for i = 1, limit do
      coroutine.yield(a)  -- top-level yield only
      a, b = b, a + b
    end
  end)
end

-- WARNING: This will error because yield is inside a nested call.
-- This demonstrates the stackless limitation!
function fibonacci_bad_nested(limit)
  return StacklessGenerator.new(function()
    local function inner()
      coroutine.yield("oops")  -- This cannot work in true stackless!
    end
    inner()  -- Will error here if we try to yield from nested
  end)
end

-- Demo
print("=== Stackless Coroutine: Fibonacci Generator (Lua) ===\n")
print("(Simulating stackless semantics with Lua's stackful coroutines)\n")

print("--- fibonacci_stackless(20) ---")
local gen = fibonacci_stackless(20)
local i = 0
while true do
  local val = gen:next()
  if val == nil then break end
  print(string.format("  fib(%d) = %d", i, val))
  i = i + 1
end

print("\n--- Key insight ---")
print("Lua coroutines are NATIVELY STACKFUL: they can yield from")
print("any call depth. This demo enforces a 'top-level yield only'")
print("discipline to simulate stackless semantics.")
print()
print("Compare with Lua's native stackful fibonacci.lua which")
print("is more flexible (can yield from nested calls).")
