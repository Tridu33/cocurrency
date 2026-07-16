/**
 * ChannelDemo.java
 *
 * Paradigm: CSP (Communicating Sequential Processes) via BlockingQueue
 *
 * Implements a CSP-style channel using Java's LinkedBlockingQueue.
 * Demonstrates unbuffered (rendezvous) and buffered communication
 * between producer and consumer threads.
 *
 * Compare with: Go channel, Python channel_demo.py
 *
 * Compile:  javac csp/ChannelDemo.java
 * Run:      cd csp && java ChannelDemo
 */

import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

public class ChannelDemo {

    // ---------------------------------------------------------------
    // Simple channel wrapper
    // ---------------------------------------------------------------
    static class Channel<T> {
        private final BlockingQueue<T> queue;

        public Channel() {
            this(0);  // unbuffered by default
        }

        public Channel(int capacity) {
            this.queue = capacity > 0
                ? new LinkedBlockingQueue<>(capacity)
                : new LinkedBlockingQueue<>(1);
        }

        /** Send — blocks until the value is received (unbuffered) or enqueued (buffered). */
        public void send(T item) throws InterruptedException {
            queue.put(item);
        }

        /** Receive — blocks until a value is available. */
        public T recv() throws InterruptedException {
            return queue.take();
        }

        /** Non-blocking send. */
        public boolean trySend(T item) {
            return queue.offer(item);
        }

        /** Non-blocking receive. */
        public T tryRecv() {
            return queue.poll();
        }

        public int size() {
            return queue.size();
        }
    }

    // ---------------------------------------------------------------
    // Demo 1: Unbuffered channel (synchronous handoff)
    // ---------------------------------------------------------------
    static void demoUnbuffered() throws InterruptedException {
        System.out.println("=== Unbuffered Channel (Rendezvous) ===");
        Channel<Integer> ch = new Channel<>();

        Thread producer = new Thread(() -> {
            try {
                for (int i = 0; i < 5; i++) {
                    int val = i * 10;
                    System.out.println("  Producer sending: " + val);
                    ch.send(val);  // blocks until consumer receives
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Producer");

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 0; i < 5; i++) {
                    int val = ch.recv();
                    System.out.println("  Consumer received: " + val);
                    Thread.sleep(50);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Consumer");

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
        System.out.println();
    }

    // ---------------------------------------------------------------
    // Demo 2: Buffered channel
    // ---------------------------------------------------------------
    static void demoBuffered() throws InterruptedException {
        System.out.println("=== Buffered Channel (capacity=3) ===");
        Channel<Integer> ch = new Channel<>(3);

        Thread producer = new Thread(() -> {
            try {
                for (int i = 0; i < 6; i++) {
                    ch.send(i);
                    System.out.println("  Produced " + i + " (buffer=" + ch.size() + "/3)");
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Producer");

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 0; i < 6; i++) {
                    int val = ch.recv();
                    System.out.println("  Consumed " + val);
                    Thread.sleep(100);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Consumer");

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
        System.out.println();
    }

    // ---------------------------------------------------------------
    // Main
    // ---------------------------------------------------------------
    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== CSP Channel Demo (Java) ===\n");
        System.out.println("BlockingQueue + Thread 实现 CSP 风格的通道通信\n");

        demoUnbuffered();
        demoBuffered();

        System.out.println("=== Key insight ===");
        System.out.println("Java's BlockingQueue.put/take provides the same");
        System.out.println("synchronous communication semantics as Go's channel.");
        System.out.println("The main difference: Java has no select{} statement.");
    }
}
