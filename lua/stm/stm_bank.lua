--[[
  stm_bank.lua
  Simulate STM (Software Transactional Memory) using coroutines.

  Implements TVar-like transactional variables with versioning,
  atomically() for transactions, and retry on conflict.
  Compare with: Python stm_model.py, Haskell STMBank.hs
]]

local STM = {}
STM.__index = STM

-- TVar: transactional variable with versioning
local TVar = {}
TVar.__index = TVar

function TVar.new(value)
  return setmetatable({
    value = value,
    version = 0
  }, TVar)
end

-- Transaction: tracks reads and writes
local Transaction = {}
Transaction.__index = Transaction

function Transaction.new()
  return setmetatable({
    read_set = {},  -- tvar -> {value, version}
    write_set = {}, -- tvar -> new_value
    should_retry = false
  }, Transaction)
end

function Transaction:read_tvar(tvar)
  if self.write_set[tvar] ~= nil then
    return self.write_set[tvar]
  end
  self.read_set[tvar] = { value = tvar.value, version = tvar.version }
  return tvar.value
end

function Transaction:write_tvar(tvar, value)
  self.write_set[tvar] = value
end

function Transaction:validate()
  for tvar, snapshot in pairs(self.read_set) do
    if tvar.version ~= snapshot.version then
      return false
    end
  end
  return true
end

function Transaction:commit()
  for tvar, new_value in pairs(self.write_set) do
    tvar.value = new_value
    tvar.version = tvar.version + 1
  end
end

-- Global transaction execution
function atomically(fn)
  while true do
    local txn = Transaction.new()
    local ok, result = pcall(fn, txn)

    if not ok then
      -- Retry on conflict
      coroutine.yield("retry")
    else
      if txn:validate() then
        txn:commit()
        return result
      end
    end
    -- Yield before retry
    coroutine.yield("conflict")
  end
end

-- Application: bank transfer with STM
local function bank_transfer(from, to, amount)
  return atomically(function(txn)
    local from_bal = txn:read_tvar(from)
    local to_bal = txn:read_tvar(to)

    if from_bal < amount then
      error("insufficient funds")
    end

    txn:write_tvar(from, from_bal - amount)
    txn:write_tvar(to, to_bal + amount)
    return string.format("Transferred %d", amount)
  end)
end

-- Demo
print("=== STM: Bank Transfer Demo (Lua) ===\n")

local acc_a = TVar.new(1000)
local acc_b = TVar.new(500)
local total_initial = acc_a.value + acc_b.value

print(string.format("Initial: A=%d, B=%d, total=%d\n", acc_a.value, acc_b.value, total_initial))

-- Create concurrent transaction coroutines
local transactions = {}
for i = 1, 5 do
  table.insert(transactions, coroutine.create(function()
    for j = 1, 3 do
      local result = bank_transfer(acc_a, acc_b, 50)
      print("  " .. result)
      coroutine.yield()
    end
  end))
end

-- Round-robin scheduler
local running = true
while running do
  running = false
  for _, co in ipairs(transactions) do
    local status = coroutine.status(co)
    if status == "suspended" or status == "running" then
      running = true
      local ok, err = coroutine.resume(co)
      if not ok and err ~= "retry" and err ~= "conflict" then
        print("  Transaction error: " .. tostring(err))
      end
    end
  end
end

local total_final = acc_a.value + acc_b.value
print(string.format("\nFinal: A=%d, B=%d, total=%d", acc_a.value, acc_b.value, total_final))
print(string.format("Total conserved: %s", (total_final == total_initial) and "YES" or "NO"))

print("\nSTM demo passed.")
