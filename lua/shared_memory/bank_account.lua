--[[
  bank_account.lua
  Simulate shared-memory bank account using coroutines for cooperative concurrency.

  Lua is single-threaded — all "concurrency" is simulated with
  coroutine.yield/resume switching.
  Compare with: Python bank_account.py, Java BankAccount
]]

local function create_account(id, initial_balance)
  return {
    id = id,
    balance = initial_balance,
    locked = false
  }
end

local function deposit(acc, amount)
  -- Simulate locking
  while acc.locked do
    coroutine.yield("waiting for lock")
  end
  acc.locked = true
  acc.balance = acc.balance + amount
  print(string.format("  [%s] deposited %d, balance=%d", acc.id, amount, acc.balance))
  acc.locked = false
  return true
end

local function withdraw(acc, amount)
  while acc.locked do
    coroutine.yield("waiting for lock")
  end
  acc.locked = true
  if acc.balance >= amount then
    acc.balance = acc.balance - amount
    print(string.format("  [%s] withdrew %d, balance=%d", acc.id, amount, acc.balance))
    acc.locked = false
    return true
  else
    print(string.format("  [%s] insufficient funds: need %d, have %d", acc.id, amount, acc.balance))
    acc.locked = false
    return false
  end
end

local function transfer(from_acc, to_acc, amount)
  -- Fixed-order locking by id to prevent deadlock
  local first, second
  if from_acc.id < to_acc.id then
    first, second = from_acc, to_acc
  else
    first, second = to_acc, from_acc
  end

  while first.locked or second.locked do
    coroutine.yield("waiting for lock")
  end
  first.locked = true
  second.locked = true

  if first.balance >= amount then
    first.balance = first.balance - amount
    second.balance = second.balance + amount
    print(string.format("  [transfer] %d from %s to %s", amount, from_acc.id, to_acc.id))
    first.locked = false
    second.locked = false
    return true
  else
    print(string.format("  [transfer] failed: insufficient funds in %s", first.id))
    first.locked = false
    second.locked = false
    return false
  end
end

-- Demo: coroutine-based concurrent transactions
local function demo_bank_account()
  local acc_a = create_account("Alice", 1000)
  local acc_b = create_account("Bob", 500)

  print("=== Shared Memory: Bank Account Demo ===\n")
  print(string.format("Initial: A=%d, B=%d, total=%d\n", acc_a.balance, acc_b.balance, acc_a.balance + acc_b.balance))

  -- Create coroutines that simulate concurrent transactions
  local threads = {}
  for i = 1, 5 do
    table.insert(threads, coroutine.create(function()
      for j = 1, 3 do
        local ok = deposit(acc_a, 50)
        coroutine.yield()
      end
    end))
  end

  for i = 1, 3 do
    table.insert(threads, coroutine.create(function()
      for j = 1, 2 do
        local ok = transfer(acc_a, acc_b, 30)
        coroutine.yield()
      end
    end))
  end

  -- Round-robin scheduler
  local running = true
  while running do
    running = false
    for _, co in ipairs(threads) do
      if coroutine.status(co) == "suspended" then
        running = true
        coroutine.resume(co)
      elseif coroutine.status(co) == "dead" then
        -- skip
      end
    end
  end

  print(string.format("\nFinal: A=%d, B=%d, total=%d", acc_a.balance, acc_b.balance, acc_a.balance + acc_b.balance))
  print("All bank account transactions simulated.\n")
end

demo_bank_account()
