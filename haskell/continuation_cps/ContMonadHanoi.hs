-----------------------------------------------------------------------------
-- ContMonadHanoi.hs -- Tower of Hanoi via the Cont Monad (CPS)
--
-- Paradigm: Continuation-Passing Style (CPS) via the Cont monad
--
-- This file demonstrates three implementations of Tower of Hanoi:
--   1. Classic direct-style recursion
--   2. Cont monad (sequentialized via continuations)
--   3. Explicit CPS (manual continuation passing)
--
-- The Cont monad transforms recursive calls into continuation-passing
-- style, making the flow of control explicit. Each recursive call is
-- given a continuation that receives its result and proceeds with the
-- rest of the computation.
--
-- Build:
--   ghc -O2 -o ContMonadHanoi ContMonadHanoi.hs
--
-- Run:
--   ./ContMonadHanoi
-----------------------------------------------------------------------------

module Main where

import Control.Monad.Cont (Cont, runCont)
import Text.Printf (printf)

-----------------------------------------------------------------------------
-- 1. Classic Tower of Hanoi (direct style)
-----------------------------------------------------------------------------

-- | Solve Tower of Hanoi recursively.
--   Parameters:
--     n   - number of disks
--     src - source peg
--     dst - destination peg
--     aux - auxiliary peg
--   Returns: list of moves as (from, to) pairs
hanoiDirect :: Int -> Char -> Char -> Char -> [(Char, Char)]
hanoiDirect 0 _ _ _ = []
hanoiDirect n src dst aux =
    hanoiDirect (n - 1) src aux dst
    ++ [(src, dst)]
    ++ hanoiDirect (n - 1) aux dst src

-----------------------------------------------------------------------------
-- 2. Tower of Hanoi using the Cont monad
--
-- The Cont monad encodes continuation-passing style. The type:
--   Cont r a  ~  (a -> r) -> r
-- meaning a value of type 'Cont r a' is a function that takes a
-- continuation (a -> r) and calls it with the result.
--
-- By sequencing Cont computations with (>>=), we make the control
-- flow explicit: each step receives the result of the previous step
-- as its continuation argument.
-----------------------------------------------------------------------------

-- | Hanoi expressed in the Cont monad.
-- The structure mirrors hanoiDirect exactly, but the recursion is
-- mediated by continuations, making the order of evaluation explicit.
hanoiCont :: Int -> Char -> Char -> Char -> Cont r [(Char, Char)]
hanoiCont 0 _ _ _ = return []
hanoiCont n src dst aux = do
    left  <- hanoiCont (n - 1) src aux dst
    let mid = [(src, dst)]
    right <- hanoiCont (n - 1) aux dst src
    return $ left ++ mid ++ right

-- | Run the Cont version with an initial identity continuation.
-- 'runCont' unwraps the Cont computation and applies the final
-- continuation.  Using 'id' as the final continuation means
-- "return the result as-is".
hanoiContRun :: Int -> Char -> Char -> Char -> [(Char, Char)]
hanoiContRun n src dst aux = runCont (hanoiCont n src dst aux) id

-----------------------------------------------------------------------------
-- 3. Explicit CPS (without the Cont monad wrapper)
--
-- This shows what the Cont monad is doing under the hood.
-- Each function takes an extra 'k' argument (the continuation)
-- and passes its result to k.
-----------------------------------------------------------------------------

-- | Explicit CPS version of Tower of Hanoi.
--   hanoiExplicit n src dst aux k = ...
--   where k is called with the result list.
hanoiExplicitCPS :: Int -> Char -> Char -> Char -> ([(Char, Char)] -> r) -> r
hanoiExplicitCPS 0 _ _ _ k = k []
hanoiExplicitCPS n src dst aux k =
    hanoiExplicitCPS (n - 1) src aux dst $ \left ->
    let mid = [(src, dst)]
    in hanoiExplicitCPS (n - 1) aux dst src $ \right ->
       k (left ++ mid ++ right)

-----------------------------------------------------------------------------
-- Pretty-printing
-----------------------------------------------------------------------------

-- | Format a single move as a string.
showMove :: (Char, Char) -> String
showMove (from, to) = [from, '-', '>', to]

-- | Format a list of moves for display.
showMoves :: [(Char, Char)] -> String
showMoves moves = unlines $ map (\(i, m) -> printf "    %2d: %s" (i :: Int) (showMove m)) (zip [1 ..] moves)

-----------------------------------------------------------------------------
-- Main
-----------------------------------------------------------------------------

main :: IO ()
main = do
    putStrLn "=============================================="
    putStrLn "  Tower of Hanoi via Continuation-Passing Style"
    putStrLn "=============================================="
    putStrLn ""

    let numDisks = 3

    putStrLn $ "Solving Tower of Hanoi with " ++ show numDisks ++ " disks..."
    putStrLn "Pegs: A (source), C (destination), B (auxiliary)"
    putStrLn ""

    -- 1. Direct style
    putStrLn "--- Direct-style recursion ---"
    let movesDirect = hanoiDirect numDisks 'A' 'C' 'B'
    putStrLn $ "Number of moves: " ++ show (length movesDirect)
    putStrLn $ showMoves movesDirect

    -- 2. Cont monad
    putStrLn "--- Cont monad ---"
    let movesCont = hanoiContRun numDisks 'A' 'C' 'B'
    putStrLn $ "Number of moves: " ++ show (length movesCont)
    putStrLn $ showMoves movesCont

    -- 3. Explicit CPS
    putStrLn "--- Explicit CPS ---"
    let movesCPS = hanoiExplicitCPS numDisks 'A' 'C' 'B' id
    putStrLn $ "Number of moves: " ++ show (length movesCPS)
    putStrLn $ showMoves movesCPS

    -- Verification
    putStrLn "--- Verification ---"
    let allMatch = movesDirect == movesCont && movesCont == movesCPS
    if allMatch
        then do
            putStrLn "All three implementations produce identical results."
            putStrLn ""
            putStrLn "Key insight: The Cont monad reifies 'what happens next'"
            putStrLn "as an explicit value (the continuation). This allows"
            putStrLn "programmers to capture, compose, and manipulate control"
            putStrLn "flow as first-class values."
        else do
            putStrLn "ERROR: Implementations disagree!"
            putStrLn $ "  Direct length: " ++ show (length movesDirect)
            putStrLn $ "  Cont    length: " ++ show (length movesCont)
            putStrLn $ "  CPS     length: " ++ show (length movesCPS)
