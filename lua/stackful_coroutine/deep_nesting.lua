--[[
  deep_nesting.lua
  Demonstrate Lua's stackful coroutines: a coroutine can yield from
  arbitrarily deep nested function calls, not just from the top-level
  function passed to coroutine.create.  This is "stackful" -- the
  entire call stack is saved and restored across a yield/resume cycle.

  Many languages with generators (Python, JavaScript) only allow yield
  directly in the generator function body (stackless).  Lua lets you
  yield from any depth, which makes coroutines far more composable.
]]

local depth = 0

function level_k(k)
    depth = depth + 1
    local prefix = string.rep("  ", depth)
    print(prefix .. "enter level_" .. k .. "  (depth=" .. depth .. ")")

    if k == 0 then
        -- Yield from the bottom of the call chain
        print(prefix .. "  >> yielding from level_0 <<")
        coroutine.yield("yielded-at-level-0")
    else
        local msg = level_k(k - 1)
        print(prefix .. "  resumed with: " .. tostring(msg))
    end

    depth = depth - 1
    print(prefix .. "leave level_" .. k)
    return "ret-val-lvl" .. k
end

-- Wrapper: the coroutine body
function nested_worker(n)
    print("[coroutine] starting, will nest " .. n .. " levels deep\n")
    local result = level_k(n)
    print("\n[coroutine] final result: " .. tostring(result))
    return result
end

-- --- Main ---
print("--- Stackful Coroutine: Deep Nesting ---\n")

local co = coroutine.create(nested_worker)
local ok, msg = coroutine.resume(co, 4)

if ok then
    print("\n[main] got from yield: " .. tostring(msg))
    print("[main] resuming coroutine to let it finish...\n")
    ok, msg = coroutine.resume(co)
    if ok then
        print("[main] coroutine finished, final status: " ..
              tostring(coroutine.status(co)))
    else
        print("[main] coroutine error: " .. tostring(msg))
    end
else
    print("[main] coroutine error: " .. tostring(msg))
end
