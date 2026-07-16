-----------------------------------------------------------------------------
-- PrintServer.hs — Actor model via MVar mailbox
--
-- Paradigm: Actor model (simulated via MVar channels)
--
-- Each actor runs in its own lightweight thread (forkIO) and processes
-- messages from an MVar-based mailbox.
--
-- Compare with: Python actor_print_server.py, Erlang gen_server
--
-- Build:
--   ghc -O2 -threaded -o PrintServer PrintServer.hs
--
-- Run:
--   ./PrintServer
-----------------------------------------------------------------------------

module Main where

import Control.Concurrent (forkIO, threadDelay, myThreadId)
import Control.Concurrent.MVar (MVar, newMVar, newEmptyMVar, putMVar, takeMVar, tryTakeMVar)
import Control.Monad (forever, void)
import Text.Printf (printf)

-----------------------------------------------------------------------------
-- Message types
-----------------------------------------------------------------------------

data Message
    = PrintJob String (MVar String)  -- text + reply channel
    | Shutdown

-----------------------------------------------------------------------------
-- Actor: PrintServer
-----------------------------------------------------------------------------

-- | Start a print-server actor. Returns the mailbox (send channel).
startPrintServer :: IO (MVar Message)
startPrintServer = do
    mailbox <- newMVar []  -- used as a queue: we'll use newEmptyMVar + manual queue
    -- Actually, MVar holds at most one value. Let's use a different approach:
    -- Use a simple MVar as a single-slot mailbox with a daemon thread.
    -- For an actual queue, we'd need Chan or TQueue, but for simplicity:
    msgSlot <- newEmptyMVar
    _ <- forkIO $ printServerLoop msgSlot 0
    return msgSlot

-- | Better: use a Chan-like pattern with an MVar of a list (acting as buffer).
-- Since MVar can hold one value, we store the whole queue as a list.

-- Actually, let's use a simple approach: the message slot is an MVar.
-- The server takes and processes one message at a time.

type Mailbox = MVar Message

printServerLoop :: Mailbox -> Int -> IO ()
printServerLoop mailbox counter = do
    msg <- takeMVar mailbox
    case msg of
        PrintJob text reply -> do
            let count = counter + 1
            threadDelay 20000  -- simulate processing
            let output = "[PrintServer] #" ++ show count ++ " printed: " ++ text
            putStrLn $ "  " ++ output
            putMVar reply output
            printServerLoop mailbox count
        Shutdown -> do
            putStrLn "  [PrintServer] shutting down"

-- | Fire-and-forget: send a message with no reply.
tell :: Mailbox -> String -> IO ()
tell mailbox text = do
    reply <- newEmptyMVar
    putMVar mailbox (PrintJob text reply)
    void $ tryTakeMVar reply  -- discard reply

-- | Request-response: send and wait for reply.
ask :: Mailbox -> String -> IO String
ask mailbox text = do
    reply <- newEmptyMVar
    putMVar mailbox (PrintJob text reply)
    takeMVar reply

-- | Send shutdown signal.
shutdown :: Mailbox -> IO ()
shutdown mailbox = do
    putMVar mailbox Shutdown

-----------------------------------------------------------------------------
-- Demo
-----------------------------------------------------------------------------

main :: IO ()
main = do
    putStrLn "=============================================="
    putStrLn "  Actor: PrintServer via MVar"
    putStrLn "=============================================="
    putStrLn ""

    server <- startPrintServer
    putStrLn "  [Main] PrintServer started"

    -- Fire-and-forget
    tell server "Hello, Haskell Actor!"
    tell server "Printing document #1"
    tell server "Printing document #2"

    threadDelay 100000

    -- Request-response
    reply <- ask server "Urgent report"
    putStrLn $ "  [Main] got reply: " ++ reply

    threadDelay 50000

    tell server "Final document"

    threadDelay 100000
    shutdown server

    putStrLn ""
    putStrLn "PrintServer demo passed."
    putStrLn ""
    putStrLn "Key insight: Each actor is a lightweight thread (forkIO)"
    putStrLn "with an MVar mailbox. Messages arrive asynchronously and"
    putStrLn "are processed sequentially — the same model as Erlang's"
    putStrLn "gen_server, but built from Haskell's concurrency primitives."
