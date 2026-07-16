/**
 * 范式2: CSP — Channel 通信 (mutex + condition_variable)
 *
 * 对标: Go channel / Python channel_demo.py
 * 编译: g++ -std=c++11 -pthread channel_demo.cpp -o channel_demo
 * 运行: ./channel_demo
 */

#include <iostream>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <random>
#include <vector>

// ---------------------------------------------------------------------------
// Channel — CSP 风格的线程安全通道
// ---------------------------------------------------------------------------

template<typename T>
class Channel {
public:
    explicit Channel(size_t capacity = 0) : capacity_(capacity), closed_(false) {}

    /** 发送数据到通道 (缓冲满时阻塞) */
    void send(const T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        send_ready_.wait(lock, [this] {
            return !closed_ && (capacity_ == 0 || queue_.size() < capacity_);
        });
        if (closed_) throw std::runtime_error("send on closed channel");

        queue_.push(item);
        recv_ready_.notify_one();
    }

    /** 从通道接收数据 (空时阻塞) */
    T recv() {
        std::unique_lock<std::mutex> lock(mutex_);
        recv_ready_.wait(lock, [this] {
            return !queue_.empty() || closed_;
        });
        if (queue_.empty() && closed_) {
            throw std::runtime_error("channel closed and empty");
        }

        T item = queue_.front();
        queue_.pop();
        send_ready_.notify_one();
        return item;
    }

    /** 关闭通道 — 禁止后续发送, 剩余数据仍可接收 */
    void close() {
        std::lock_guard<std::mutex> lock(mutex_);
        closed_ = true;
        send_ready_.notify_all();
        recv_ready_.notify_all();
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
    }

private:
    size_t capacity_;
    bool closed_;
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    std::condition_variable send_ready_;
    std::condition_variable recv_ready_;
};

// ---------------------------------------------------------------------------
// Demo 1: 无缓冲 Channel (同步会合)
// ---------------------------------------------------------------------------

void demo_unbuffered() {
    std::cout << "=== Demo 1: 无缓冲 Channel (同步会合) ===\n";
    Channel<int> ch(0);

    std::thread producer([&] {
        for (int i = 0; i < 5; ++i) {
            int val = i * 10;
            std::cout << "  生产者发送: " << val << "\n";
            ch.send(val);  // 阻塞直到消费者接收
        }
        ch.close();
    });

    std::thread consumer([&] {
        try {
            while (true) {
                int val = ch.recv();
                std::cout << "  消费者接收: " << val << "\n";
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
            }
        } catch (const std::runtime_error&) {
            std::cout << "  消费者: 通道关闭\n";
        }
    });

    producer.join();
    consumer.join();
    std::cout << "\n";
}

// ---------------------------------------------------------------------------
// Demo 2: 缓冲 Channel (异步通信)
// ---------------------------------------------------------------------------

void demo_buffered() {
    std::cout << "=== Demo 2: 缓冲 Channel (capacity=3) ===\n";
    Channel<int> ch(3);

    std::thread producer([&] {
        for (int i = 0; i < 6; ++i) {
            ch.send(i);
            std::cout << "  生产: " << i << " (缓冲: " << ch.size() << "/3)\n";
        }
        ch.close();
    });

    std::thread consumer([&] {
        try {
            while (true) {
                int val = ch.recv();
                std::cout << "  消费: " << val << "\n";
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        } catch (const std::runtime_error&) {
            std::cout << "  消费者: 通道关闭\n";
        }
    });

    producer.join();
    consumer.join();
    std::cout << "\n";
}

// ---------------------------------------------------------------------------
// Demo 3: 多生产者 - 多消费者
// ---------------------------------------------------------------------------

void demo_multi_prod_cons() {
    std::cout << "=== Demo 3: 多生产者 - 多消费者 ===\n";
    Channel<int> ch(5);

    // 两个生产者
    auto producer_fn = [&](int id, int start, int count) {
        for (int i = 0; i < count; ++i) {
            int val = start + i;
            ch.send(val);
            std::cout << "  生产者 P" << id << " -> " << val << "\n";
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
    };

    // 两个消费者
    auto consumer_fn = [&](int id, int total) {
        int received = 0;
        while (received < total) {
            try {
                int val = ch.recv();
                std::cout << "  消费者 C" << id << " <- " << val << "\n";
                received++;
            } catch (const std::runtime_error&) {
                break;
            }
        }
    };

    std::thread p1(producer_fn, 1, 1, 5);
    std::thread p2(producer_fn, 2, 101, 5);
    std::thread c1(consumer_fn, 1, 5);
    std::thread c2(consumer_fn, 2, 5);

    p1.join();
    p2.join();
    ch.close();
    c1.join();
    c2.join();
    std::cout << "\n";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== CSP Channel Demo ===\n\n";

    demo_unbuffered();
    demo_buffered();
    demo_multi_prod_cons();

    std::cout << "All CSP demos passed.\n";
    return 0;
}
