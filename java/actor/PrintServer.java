/**
 * PrintServer.java
 *
 * Paradigm: Actor Model via ExecutorService + BlockingQueue
 *
 * A thread-based actor with a message mailbox. Demonstrates:
 *   - tell():  fire-and-forget message
 *   - ask():   request-response with reply
 *   - graceful shutdown via sentinel message
 *
 * Compare with: Python actor_print_server.py, Erlang gen_server
 *
 * Compile:  javac actor/PrintServer.java
 * Run:      java actor.PrintServer
 *
 * NOTE: Use java with the actor folder on classpath.
 */

import java.util.concurrent.*;
import java.util.function.Consumer;

public class PrintServer {

    // ---- Message types ----
    interface Message { }
    static class PrintJob implements Message {
        final String text;
        final Consumer<String> replyCallback;
        PrintJob(String text, Consumer<String> replyCallback) {
            this.text = text;
            this.replyCallback = replyCallback;
        }
    }
    static class Shutdown implements Message { }

    // ---- Actor implementation ----
    private final BlockingQueue<Message> mailbox = new LinkedBlockingQueue<>();
    private final ExecutorService executor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "print-server");
        t.setDaemon(true);
        return t;
    });
    private volatile boolean running = false;

    public void start() {
        running = true;
        executor.submit(this::run);
        System.out.println("  [PrintServer] started");
    }

    /** Fire-and-forget */
    public void tell(String text) {
        mailbox.offer(new PrintJob(text, null));
    }

    /** Request-response: send and wait for reply.
     *  WARNING: Uses CompletableFuture.get() which throws checked exceptions. */
    public String ask(String text) throws Exception {
        CompletableFuture<String> future = new CompletableFuture<>();
        mailbox.offer(new PrintJob(text, reply -> future.complete(reply)));
        return future.get(5, TimeUnit.SECONDS);
    }

    public void stop() {
        mailbox.offer(new Shutdown());
        executor.shutdown();
        try {
            executor.awaitTermination(1, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        System.out.println("  [PrintServer] stopped");
    }

    private void run() {
        int counter = 0;
        try {
            while (running) {
                Message msg = mailbox.take();  // blocks
                if (msg instanceof Shutdown) {
                    running = false;
                    break;
                }
                if (msg instanceof PrintJob job) {
                    counter++;
                    Thread.sleep(20);  // simulate processing
                    String output = "[PrintServer] #" + counter + " printed: " + job.text;
                    System.out.println("  " + output);
                    if (job.replyCallback != null) {
                        job.replyCallback.accept(output);
                    }
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // ---- Demo ----
    public static void main(String[] args) throws Exception {
        System.out.println("=== Actor: PrintServer Demo ===\n");

        PrintServer server = new PrintServer();
        server.start();

        // Fire-and-forget
        server.tell("Hello, Actor World!");
        server.tell("Printing document #1");
        server.tell("Printing document #2");

        // Request-response
        String reply = server.ask("Urgent report");
        System.out.println("  [Client] got reply: " + reply);

        Thread.sleep(50);

        server.tell("Final document");
        Thread.sleep(50);
        server.stop();

        System.out.println("\nPrintServer demo passed.");
    }
}
