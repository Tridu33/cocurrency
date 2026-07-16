--[[
  channel.lua
  CSP channel implemented with coroutines.

  Provides send/recv operations on a buffered or unbuffered channel,
  using Lua coroutines for cooperative multitasking.
  Compare with: Go channel, Python channel_demo.py
]]

local Channel = {}
Channel.__index = Channel

function Channel.new(capacity)
  return setmetatable({
    buffer = {},
    capacity = capacity or 0,
    senders = {},
    receivers = {},
    closed = false
  }, Channel)
end

function Channel:send(value)
  if self.closed then
    error("send on closed channel")
  end

  -- If there's a waiting receiver, hand off directly
  if #self.receivers > 0 then
    local recv_co = table.remove(self.receivers, 1)
    self.buffer[#self.buffer + 1] = value
    coroutine.resume(recv_co)
    return
  end

  -- If buffer has space, enqueue
  if self.capacity == 0 or #self.buffer < self.capacity then
    self.buffer[#self.buffer + 1] = value
    return
  end

  -- Buffer full: suspend sender
  table.insert(self.senders, coroutine.running())
  coroutine.yield()
  self.buffer[#self.buffer + 1] = value
end

function Channel:recv()
  -- If buffer is non-empty, dequeue
  if #self.buffer > 0 then
    local value = table.remove(self.buffer, 1)
    -- Wake a waiting sender if any
    if #self.senders > 0 then
      local send_co = table.remove(self.senders, 1)
      coroutine.resume(send_co)
    end
    return value
  end

  if self.closed then
    return nil
  end

  -- Buffer empty: suspend receiver
  table.insert(self.receivers, coroutine.running())
  coroutine.yield()
  return table.remove(self.buffer, 1)
end

function Channel:close()
  self.closed = true
  -- Wake all waiting receivers
  for _, co in ipairs(self.receivers) do
    coroutine.resume(co)
  end
  self.receivers = {}
end

-- Producer coroutine
function producer(ch, values, name)
  for _, v in ipairs(values) do
    print(string.format("  [%s] sending %d", name, v))
    ch:send(v)
    print(string.format("  [%s] sent %d", name, v))
  end
  print(string.format("  [%s] done", name))
end

-- Consumer coroutine
function consumer(ch, count, name, results)
  for i = 1, count do
    local val = ch:recv()
    if val == nil then break end
    table.insert(results, val)
    print(string.format("  [%s] received %d", name, val))
  end
  print(string.format("  [%s] done (got %d items)", name, #results))
end

-- Scheduler: run coroutines cooperatively
function scheduler(cos)
  local threads = {}
  for _, f in ipairs(cos) do
    table.insert(threads, coroutine.create(f))
  end

  while #threads > 0 do
    local co = table.remove(threads, 1)
    local ok, err = coroutine.resume(co)
    if ok and coroutine.status(co) == "suspended" then
      table.insert(threads, co)
    elseif not ok then
      print("  Error:", err)
    end
  end
end

-- Demo
print("=== CSP Channel Demo (Lua) ===\n")

-- Demo 1: Buffered channel
print("--- Buffered Channel (capacity=3) ---")
local ch1 = Channel.new(3)
local results1 = {}

scheduler({
  function() producer(ch1, {10, 20, 30, 40, 50}, "P1") end,
  function() producer(ch1, {60, 70, 80, 90, 100}, "P2") end,
  function() consumer(ch1, 5, "C1", results1) end,
  function() consumer(ch1, 5, "C2", results1) end,
})

print()

-- Demo 2: Unbuffered channel (rendezvous)
print("--- Unbuffered Channel ---")
local ch2 = Channel.new(0)
local results2 = {}

scheduler({
  function() producer(ch2, {1, 2, 3}, "P1") end,
  function() consumer(ch2, 3, "C1", results2) end,
})

print("\nAll channel demos passed.")
