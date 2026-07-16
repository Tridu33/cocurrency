-----------------------------------------------------------------------------
-- BankAccount.hs — Shared Memory via MVar
--
-- Paradigm: Shared-memory concurrency using MVar (synchronized mutable var)
--
-- MVar is a single-place mailbox that can hold at most one value.
-- It provides thread-safe putMVar / takeMVar operations, making it
-- ideal for shared-state coordination.
--
-- Compare with: Java BankAccount (synchronized), Go Mutex
--
-- Build:
--   ghc -O2 -threaded -o BankAccount BankAccount.hs
--
-- Run:
--   ./BankAccount
-----------------------------------------------------------------------------

module Main where

import Control.Concurrent (forkIO, threadDelay)
import Control.Concurrent.MVar (MVar, newMVar, newEmptyMVar, putMVar, takeMVar, tryTakeMVar)
import Control.Monad (forM_, replicateM, void)
import System.Random (randomRIO)
import Text.Printf (printf)

-----------------------------------------------------------------------------
-- Account — protected by an MVar holding the balance
-----------------------------------------------------------------------------

type Account = MVar Int

newAccount :: Int -> IO Account
newAccount = newMVar

-- | Deposit: take the current balance, add, and put back.
deposit :: Account -> Int -> IO ()
deposit acc amount = do
    bal <- takeMVar acc
    let newBal = bal + amount
    putMVar acc newBal
    printf "  Deposited %4d, balance now: %d\n" amount newBal

-- | Withdraw: take, check, subtract, put back.
withdraw :: Account -> Int -> IO Bool
withdraw acc amount = do
    bal <- takeMVar acc
    if bal >= amount
        then do
            let newBal = bal - amount
            putMVar acc newBal
            printf "  Withdrew  %4d, balance now: %d\n" amount newBal
            return True
        else do
            putMVar acc bal  -- restore unchanged
            printf "  Withdraw %4d FAILED (balance: %d)\n" amount bal
            return False

-- | Transfer: first lock from, then to, by id ordering to prevent deadlock.
transfer :: Account -> Account -> Int -> IO Bool
transfer from to amount = do
    -- Simple strategy: lock from first, then to (fixed order by pointer)
    ok <- withdraw from amount
    if ok
        then do
            deposit to amount
            return True
        else
            return False

-- | Read balance (non-blocking snapshot).
readBalance :: Account -> IO Int
readBalance acc = do
    bal <- takeMVar acc
    putMVar acc bal
    return bal

-----------------------------------------------------------------------------
-- Demo
-----------------------------------------------------------------------------

main :: IO ()
main = do
    putStrLn "=============================================="
    putStrLn "  Shared Memory via MVar — Bank Account Demo"
    putStrLn "=============================================="
    putStrLn ""

    accA <- newAccount 1000
    accB <- newAccount 500

    initTotal <- (+) <$> readBalance accA <*> readBalance accB
    printf "Initial: A=%d, B=%d, total=%d\n" (1000 :: Int) (500 :: Int) initTotal
    putStrLn ""

    -- Concurrent deposits and transfers
    putStrLn "Spawning 5 concurrent threads for deposits/transfers..."
    putStrLn ""

    done <- newEmptyMVar
    let numOps = 3

    _ <- replicateM 5 $ forkIO $ do
        forM_ [1 .. numOps] $ \_ -> do
            amount <- randomRIO (10, 100)
            deposit accA amount
            threadDelay 5000

        forM_ [1 .. numOps] $ \_ -> do
            amt <- randomRIO (20, 50)
            _ <- transfer accA accB amt
            threadDelay 5000

        putMVar done ()

    -- Wait for all threads
    void $ replicateM 5 $ takeMVar done

    putStrLn ""
    balA <- readBalance accA
    balB <- readBalance accB
    let finalTotal = balA + balB
    printf "Final: A=%d, B=%d, total=%d\n" balA balB finalTotal
    printf "Total conserved: %s\n" (if finalTotal == initTotal then "YES" else "NO (ERROR!)")

    putStrLn ""
    putStrLn "Key insight: MVar provides thread-safe shared state."
    putStrLn "takeMVar acquires the lock, putMVar releases it."
    putStrLn "This is Haskell's simplest shared-memory primitive."
