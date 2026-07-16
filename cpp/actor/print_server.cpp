/**
 * 范式3: Actor 模型 — 打印服务器 (std::thread + queue)
 *
 * 对标: Python actor_print_server.py / Erlang gen_server
 * 编译: g++ -std=c++11 -pthread print_server.cpp -o print_server
 * 运行: ./print_server
 */

#include <iostream>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <string>
#include <chrono>

// ---------------------------------------------------------------------------
// Message types
// ---------------------------------------------------------------------------

struct Message {
    enum Type { PRINT, SHUTDOWN };
    Type type;
    std::string text;
    std::function<void(std::string)> reply_callback;

    Message(Type t, const std::string& txt = "",
            std::function<void(std::string)> cb = nullptr)
        : type(t), text(txt), reply_callback(cb) {}
};

// ---------------------------------------------------------------------------
// Actor: PrintServer — 独立线程 + 消息队列
// ---------------------------------------------------------------------------

class PrintServer {
public:
    PrintServer() : running_(false) {}

    ~PrintServer() {
        if (running_) stop();
    }

    void start() {
        running_ = true;
        thread_ = std::thread(&PrintServer::run, this);
        std::cout << "  [PrintServer] started\n";
    }

    /** Fire-and-forget: 发送消息, 不等待回复 */
    void tell(const std::string& text) {
        mailbox_.push(Message(Message::PRINT, text));
    }

    /** Request-response: 发送消息并等待回复 */
    std::string ask(const std::string& text) {
        std::string reply;
        std::mutex mtx;
        std::condition_variable cv;
        bool done = false;

        mailbox_.push(Message(Message::PRINT, text,
            [&](const std::string& r) {
                std::lock_guard<std::mutex> lock(mtx);
                reply = r;
                done = true;
                cv.notify_one();
            }));

        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [&] { return done; });
        return reply;
    }

    void stop() {
        mailbox_.push(Message(Message::SHUTDOWN));
        if (thread_.joinable()) thread_.join();
        std::cout << "  [PrintServer] stopped\n";
    }

private:
    void run() {
        int counter = 0;
        while (true) {
            Message msg = mailbox_.pop();
            if (msg.type == Message::SHUTDOWN) {
                break;
            }

            // 处理打印消息
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
            std::string output = "[PrintServer] #" + std::to_string(++counter)
                               + " printed: " + msg.text;
            std::cout << "  " << output << "\n";

            if (msg.reply_callback) {
                msg.reply_callback(output);
            }
        }
    }

    // -----------------------------------------------------------------------
    // Thread-safe mailbox (bounded queue)
    // -----------------------------------------------------------------------
    class Mailbox {
    public:
        void push(const Message& msg) {
            std::lock_guard<std::mutex> lock(mutex_);
            queue_.push(msg);
            cv_.notify_one();
        }

        Message pop() {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] { return !queue_.empty(); });
            Message msg = queue_.front();
            queue_.pop();
            return msg;
        }

    private:
        std::queue<Message> queue_;
        std::mutex mutex_;
        std::condition_variable cv_;
    };

    Mailbox mailbox_;
    std::thread thread_;
    bool running_;
};

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== Actor: PrintServer Demo ===\n\n";

    PrintServer server;
    server.start();

    // Fire-and-forget
    server.tell("Hello, Actor World!");
    server.tell("Printing document #1");
    server.tell("Printing document #2");

    // Request-response
    std::string reply = server.ask("Urgent report");
    std::cout << "  [Client] got reply: " << reply << "\n";

    std::this_thread::sleep_for(std::chrono::milliseconds(50));

    // 更多 fire-and-forget
    server.tell("Final document");

    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    server.stop();

    std::cout << "\nPrintServer demo passed.\n";
    return 0;
}
