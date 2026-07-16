-----------------------------------------------------------------------------
-- STMBank.hs -- STM (Software Transactional Memory) Bank Transfer
--
-- Paradigm: Composable concurrent transactions via Software Transactional
--           Memory (STM)
--
-- GHC's STM provides composable atomic transactions using TVar (transactional
-- variables). Unlike lock-based approaches, STM operations are:
--   1. Composable  -- combine multiple TVar reads/writes atomically
--   2. Safe        -- no deadlocks or race conditions
--   3. Retry-based -- transactions retry automatically on conflict
--
-- This demo creates 5 bank accounts and spawns 7 concurrent threads that
-- perform random transfers. STM guarantees that each transfer is atomic
-- and that the total balance is always conserved.
--
-- Build:
--   ghc -O2 -threaded -package stm -o STMBank STMBank.hs
--
-- Run:
--   ./STMBank
-----------------------------------------------------------------------------

module Main where

import Control.Concurrent (forkIO)
import Control.Concurrent.MVar (newEmptyMVar, putMVar, takeMVar)
import Control.Concurrent.STM (atomically, STM)
import Control.Concurrent.STM.TVar (TVar, modifyTVar', newTVarIO, readTVar, writeTVar)
import Control.Monad (replicateM)
import System.Random (randomRIO)
import Text.Printf (printf)

-----------------------------------------------------------------------------
-- Core types and operations
-----------------------------------------------------------------------------

-- | A bank account is a 'TVar Int' holding the current balance.
-- TVar ensures that all reads and writes participate in an STM transaction.
type Account = TVar Int

-- | Create a new account with the given initial balance.
newAccount :: Int -> IO Account
newAccount = newTVarIO

-- | Read the current balance in a transaction.
readBalance :: Account -> STM Int
readBalance = readTVar

-- | Print the balance of a single account (IO action, not transactional).
printBalance :: Account -> IO Int
printBalance acc = atomically $ readTVar acc

-----------------------------------------------------------------------------
-- Transfer operations -- demonstrating STM composability
-----------------------------------------------------------------------------

-- | Atomic transfer between two accounts.
-- Both operations (debit and credit) happen in a single STM transaction.
-- No other thread can observe an intermediate state where money has been
-- debited but not yet credited.
--
-- If you tried to do this with separate locks, you would need to acquire
-- locks on both accounts, which risks deadlock. STM eliminates this problem.
transfer :: Account -> Account -> Int -> IO ()
transfer from to amount = atomically $ do
    fromBal <- readTVar from
    if fromBal < amount
        then error "Insufficient funds"
        else do
            writeTVar from (fromBal - amount)
            modifyTVar' to (+ amount)

-- | Safe version of transfer that returns a success flag instead of crashing.
-- This is still a single, atomic, composable transaction.
safeTransfer :: Account -> Account -> Int -> IO Bool
safeTransfer from to amount = atomically $ do
    fromBal <- readTVar from
    if fromBal < amount
        then return False
        else do
            writeTVar from (fromBal - amount)
            modifyTVar' to (+ amount)
            return True

-- | Atomically compute the total balance across all accounts.
-- This is a composite STM operation -- it reads multiple TVars in a single
-- transaction, guaranteeing a consistent snapshot of the system.
totalBalance :: [Account] -> IO Int
totalBalance accounts = atomically $ do
    balances <- mapM readTVar accounts
    return $ sum balances

-----------------------------------------------------------------------------
-- Transfer thread
-----------------------------------------------------------------------------

-- | Run a single thread that performs 'n' random transfers.
transferThread :: [Account] -> Int -> IO ()
transferThread accounts = go
  where
    numAccounts = length accounts

    go 0 = pure ()
    go n = do
        fromIdx <- randomRIO (0, numAccounts - 1)
        toIdx   <- randomRIO (0, numAccounts - 1)
        amt     <- randomRIO (10, 200)
        if fromIdx /= toIdx
            then do
                let fromAcc = accounts !! fromIdx
                    toAcc   = accounts !! toIdx
                _ <- safeTransfer fromAcc toAcc amt
                go (n - 1)
            else
                go n  -- retry with different accounts

-----------------------------------------------------------------------------
-- Helpers
-----------------------------------------------------------------------------

printBalances :: [Account] -> IO ()
printBalances accounts = do
    balances <- mapM printBalance accounts
    let labeled = zip [1 :: Int ..] balances
    mapM_ (\(i, b) -> printf "    Account %d: %6d\n" i b) labeled

-----------------------------------------------------------------------------
-- Main
-----------------------------------------------------------------------------

main :: IO ()
main = do
    putStrLn "=============================================="
    putStrLn "  STM Bank Transfer Demo"
    putStrLn "  Composable concurrent transactions"
    putStrLn "=============================================="
    putStrLn ""

    -- Create 5 accounts with varying balances
    a1 <- newAccount 1000
    a2 <- newAccount 2000
    a3 <- newAccount 1500
    a4 <- newAccount 3000
    a5 <- newAccount 500

    let accounts = [a1, a2, a3, a4, a5]

    putStrLn "Initial balances:"
    printBalances accounts
    initTotal <- totalBalance accounts
    putStrLn $ "  -------------------"
    printf "  Total: %6d\n" initTotal
    putStrLn ""

    -- Spawn 7 concurrent transfer threads
    let numThreads = 7
        transfersPerThread = 5

    putStrLn $ "Spawning " ++ show numThreads ++ " concurrent transfer threads"
    putStrLn $ "(each performing " ++ show transfersPerThread ++ " random transfers)..."
    putStrLn ""

    -- Use MVars to synchronize completion
    doneMVars <- replicateM numThreads $ do
        done <- newEmptyMVar
        _ <- forkIO $ transferThread accounts transfersPerThread >> putMVar done ()
        return done

    -- Wait for all threads to finish
    putStrLn "Waiting for all transfers to complete..."
    mapM_ takeMVar doneMVars
    putStrLn ""

    -- Print final state
    putStrLn "Final balances:"
    printBalances accounts
    finalTotal <- totalBalance accounts
    putStrLn $ "  -------------------"
    printf "  Total: %6d\n" finalTotal
    putStrLn ""

    -- Verify conservation
    putStrLn "Verification:"
    if initTotal == finalTotal
        then do
            putStrLn "  Total balance is CONSERVED."
            putStrLn "  STM guarantees atomicity and consistency."
            putStrLn ""
            putStrLn "  Key insight: Because each transfer is a single STM"
            putStrLn "  transaction, the system is always in a consistent"
            putStrLn "  state. No lock ordering, no deadlocks, no races."
        else
            putStrLn "  ERROR: Total balance changed -- inconsistency detected!"
