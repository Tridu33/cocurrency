--[[
  print_server.lua
  Actor-model print server using coroutines + mailbox.

  Each "actor" is a coroutine with a message queue (table).
  Supports tell (fire-and-forget) and ask (request-response).
  Compare with: Python actor_print_server.py, Erlang gen_server
]]

local PrintServer = {}
PrintServer.__index = PrintServer

function PrintServer.new()
  local self = setmetatable({
    mailbox = {},
    counter = 0,
    running = true
  }, PrintServer)

  -- The actor runs as a coroutine processing messages
  self.actor = coroutine.create(function()
    self:run()
  end)

  return self
end

function PrintServer:run()
  while self.running do
    if #self.mailbox > 0 then
      local msg = table.remove(self.mailbox, 1)
      self.counter = self.counter + 1

      -- Simulate processing
      local output = string.format("[PrintServer] #%d printed: %s", self.counter, msg.text)
      print("  " .. output)

      if msg.reply_to then
        msg.reply_to(output)
      end
    end
    coroutine.yield()
  end
  print("  [PrintServer] shutting down")
end

function PrintServer:tell(text)
  table.insert(self.mailbox, { text = text, reply_to = nil })
end

function PrintServer:ask(text)
  local result
  local done = false
  table.insert(self.mailbox, {
    text = text,
    reply_to = function(reply)
      result = reply
      done = true
    end
  })
  -- Process until we get the reply
  while not done do
    coroutine.resume(self.actor)
  end
  return result
end

function PrintServer:step()
  coroutine.resume(self.actor)
end

function PrintServer:stop()
  self.running = false
  coroutine.resume(self.actor)
end

-- Demo
print("=== Actor: PrintServer Demo (Lua) ===\n")

local server = PrintServer.new()
print("  [PrintServer] started")

-- Fire-and-forget
server:tell("Hello, Actor World!")
server:tell("Printing document #1")
server:tell("Printing document #2")
server:step() -- process one batch

-- Request-response
local reply = server:ask("Urgent report")
print("  [Client] got reply: " .. reply)

server:step()

server:tell("Final document")
server:step()
server:stop()

print("\nPrintServer demo passed.")
