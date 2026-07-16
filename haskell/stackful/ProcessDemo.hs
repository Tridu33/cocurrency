-----------------------------------------------------------------------------
-- ProcessDemo.hs -- GHC Lightweight Threads as Stackful Coroutines
--
-- Paradigm: Stackful coroutines via GHC's M:N threading
--
-- GHC implements lightweight (green) threads using an M:N scheduler:
--   M Haskell threads  ->  N OS threads (typically N = # of cores)
--
-- Each Haskell thread is a *stackful coroutine*:
--   - It has its own call stack
--   - It can be suspended at any point (e.g., waiting on an MVar)
--   - The runtime scheduler handles yielding and resumption
--   - Thousands of threads can be created with minimal overhead
--
-- This is conceptually similar to goroutines in Go or stackful
-- coroutines in C++ libraries like Boost.Fiber.
--
-- The key operations:
--   'forkIO'   -- spawn a lightweight thread
--   'MVar'     -- a synchronized mutable variable for thread communication
--                (putMVar blocks if full, takeMVar blocks if empty)
--
-- Build:
--   ghc -O2 -threaded -o ProcessDemo ProcessDemo.hs
--
-- Run:
--   ./ProcessDemo
--   ./ProcessDemo +RTS -N4   (use 4 OS threads / cores)
-----------------------------------------------------------------------------

module Main where

import Control.Concurrent (forkIO, getNumCapabilities, myThreadId, threadDelay)
import Control.Concurrent.MVar (MVar, newEmptyMVar, putMVar, takeMVar)
import Control.Monad (forM_, replicateM)
import Text.Printf (printf)
import Data.Time.Clock (getCurrentTime, diffUTCTime)

-----------------------------------------------------------------------------
-- Fibonacci (naive, CPU-bound computation)
-----------------------------------------------------------------------------

-- | Naive recursive fibonacci.
-- Intentionally slow to create a measurable CPU workload.
fib :: Integer -> Integer
fib 0 = 0
fib 1 = 1
fib n = fib (n - 1) + fib (n - 2)

-----------------------------------------------------------------------------
-- Concurrent fibonacci computation
-----------------------------------------------------------------------------

-- | Compute fib(n) in a separate lightweight thread and signal completion
-- via an MVar.  The caller can 'takeMVar' to block until the result is ready.
concurrentFib :: Integer -> IO (MVar Integer)
concurrentFib n = do
    result <- newEmptyMVar
    _ <- forkIO $ do
        tid <- myThreadId
        let r = fib n
        printf "    [Thread %s] fib(%s) = %s\n" (show tid) (show n) (show r)
        putMVar result r
    return result

-----------------------------------------------------------------------------
-- Sequential fibonacci (for comparison)
-----------------------------------------------------------------------------

sequentialFib :: Integer -> IO Integer
sequentialFib n = do
    putStrLn $ "    Computing fib(" ++ show n ++ ") sequentially..."
    let r = fib n
    putStrLn $ "    fib(" ++ show n ++ ") = " ++ show r
    return r

-----------------------------------------------------------------------------
-- M:N threading demonstration
-----------------------------------------------------------------------------

-- | Spawn multiple concurrent workers, each doing work and passing results
-- back through an MVar.  Demonstrates GHC's ability to create and manage
-- many lightweight threads.
spawnWorkers :: Int -> IO ()
spawnWorkers numWorkers = do
    putStrLn $ "Spawning " ++ show numWorkers ++ " concurrent workers..."
    results <- replicateM numWorkers $ do
        mv <- newEmptyMVar
        _ <- forkIO $ do
            tid <- myThreadId
            threadDelay 100000  -- simulate work (100 ms)
            putMVar mv tid
        return mv
    tids <- mapM takeMVar results
    putStrLn $ "All " ++ show (length tids) ++ " workers completed."
    putStrLn ""

-----------------------------------------------------------------------------
-- Main
-----------------------------------------------------------------------------

main :: IO ()
main = do
    putStrLn "=============================================="
    putStrLn "  GHC Lightweight Threads / Stackful Coroutines"
    putStrLn "=============================================="
    putStrLn ""

    -- Show thread model info
    numCaps <- getNumCapabilities
    putStrLn $ "GHC capabilities (OS threads): " ++ show numCaps
    putStrLn $ "This demonstrates M:N threading: M lightweight threads"
    putStrLn $ "are mapped onto N OS threads by the GHC runtime scheduler."
    putStrLn ""

    -------------------------------------------------------
    -- Part 1: Spawn many lightweight threads
    -------------------------------------------------------
    putStrLn "--- Part 1: Lightweight thread spawning ---"
    putStrLn "GHC can spawn millions of threads; each costs only ~1 KB."
    spawnWorkers 10

    -------------------------------------------------------
    -- Part 2: Concurrent fibonacci computation
    -------------------------------------------------------
    putStrLn "--- Part 2: Concurrent fibonacci ---"
    putStrLn "Computing several fibonacci numbers concurrently..."
    putStrLn "Each computation runs in its own lightweight thread."
    putStrLn ""

    -- Compute multiple fibonacci numbers concurrently
    let fibArgs = [35, 36, 37, 38] :: [Integer]

    putStrLn "Spawning concurrent fib computations..."
    startConc <- getCurrentTime

    mvars <- mapM concurrentFib fibArgs

    putStrLn ""
    putStrLn "Main thread is free to do other work while waiting..."
    putStrLn ""

    -- Block until all results are ready
    results <- mapM takeMVar mvars
    endConc <- getCurrentTime

    putStrLn ""
    putStrLn "Concurrent results:"
    forM_ (zip fibArgs results) $ \(n, r) ->
        printf "  fib(%d) = %d\n" (n :: Integer) (r :: Integer)

    let concTime = diffUTCTime endConc startConc
    printf "\nConcurrent time: %.2f seconds\n" (realToFrac concTime :: Double)
    putStrLn ""

    -------------------------------------------------------
    -- Part 3: Sequential comparison
    -------------------------------------------------------
    putStrLn "--- Part 3: Sequential comparison ---"
    putStrLn "Computing the same fibonacci numbers sequentially..."
    putStrLn ""

    startSeq <- getCurrentTime
    _ <- mapM sequentialFib fibArgs
    endSeq <- getCurrentTime

    let seqTime = diffUTCTime endSeq startSeq
    printf "Sequential time: %.2f seconds\n" (realToFrac seqTime :: Double)
    putStrLn ""

    -------------------------------------------------------
    -- Summary
    -------------------------------------------------------
    putStrLn "--- Summary ---"
    printf "  Concurrent: %.2f s\n" (realToFrac concTime :: Double)
    printf "  Sequential: %.2f s\n" (realToFrac seqTime :: Double)
    let speedup = realToFrac seqTime / realToFrac concTime :: Double
    printf "  Speedup: %.2fx (limited by number of cores and overhead)\n" speedup
    putStrLn ""
    putStrLn "Key insight: GHC's lightweight threads are stackful coroutines."
    putStrLn "Each thread has its own stack and can be suspended at any point"
    putStrLn "(e.g., blocking on an MVar). The runtime scheduler handles"
    putStrLn "context switching, yielding, and load balancing across OS threads."
    putStrLn "This is the same model used by Go (goroutines) and Erlang."
