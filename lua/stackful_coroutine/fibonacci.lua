--[[
  fibonacci.lua
  Generate Fibonacci numbers using a coroutine so the caller can pull
  values lazily without computing the whole sequence upfront.
]]

function fibonacci(limit)
    return coroutine.wrap(function()
        local a, b = 0, 1
        local count = 0
        while count < limit do
            coroutine.yield(a)
            a, b = b, a + b
            count = count + 1
        end
    end)
end

-- --- Main ---
local n = 10
print("First " .. n .. " Fibonacci numbers:\n")

local fib = fibonacci(n)
for num in fib do
    print("  " .. num)
end
