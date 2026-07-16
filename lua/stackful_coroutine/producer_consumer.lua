--[[
  producer_consumer.lua
  Demonstrates a producer-consumer pattern using Lua's coroutine.create,
  coroutine.resume, and coroutine.yield.

  The producer coroutine generates items on demand, and the consumer
  requests them one at a time.  Control flips between the two coroutines
  via yield/resume -- no explicit buffers or locking needed.
]]

-- Producer: yields values one at a time
function producer()
    local i = 1
    while true do
        local value = "item-" .. i
        print("  [producer] generated " .. value)
        coroutine.yield(value)
        i = i + 1
    end
end

-- Consumer: pulls a requested number of items from the producer
function consume(prod_co, count)
    print("[consumer] starting, will consume " .. count .. " items\n")
    local results = {}
    for _ = 1, count do
        local ok, val = coroutine.resume(prod_co)
        if not ok then
            error("producer failed: " .. tostring(val))
        end
        print("[consumer] received " .. val)
        table.insert(results, val)
    end
    print("\n[consumer] done, collected " .. #results .. " items")
    return results
end

-- --- Main ---
local prod_co = coroutine.create(producer)
consume(prod_co, 5)

-- The producer coroutine is still alive: we could consume more items.
-- Lua's GC will clean it up when no references remain.
