/**
 * 范式1: 共享内存 + 锁 — 生产者消费者 (C++11 mutex + condition_variable)
 *
 * 编译: g++ -std=c++11 -pthread producer_consumer.cpp -o producer_consumer
 * 运行: ./producer_consumer
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <chrono>
#include <random>

std::mutex mtx;
std::condition_variable cv;
std::queue<int> buffer;
const unsigned int MAX_BUFFER = 5;
bool done = false;

std::random_device rd;
std::mt19937 gen(rd());
std::uniform_int_distribution<> dis(100, 500);

void producer(int id) {
    for (int i = 0; i < 10; ++i) {
        std::this_thread::sleep_for(std::chrono::milliseconds(dis(gen)));

        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [] { return buffer.size() < MAX_BUFFER; });

        int item = i + id * 100;
        buffer.push(item);
        std::cout << "生产者 " << id << " 生产: " << item
                  << " (队列大小: " << buffer.size() << ")\n";

        lock.unlock();
        cv.notify_all();
    }
}

void consumer(int id) {
    while (true) {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [] { return !buffer.empty() || done; });

        if (buffer.empty() && done) break;

        int item = buffer.front();
        buffer.pop();
        std::cout << "消费者 " << id << " 消费: " << item
                  << " (队列大小: " << buffer.size() << ")\n";

        lock.unlock();
        cv.notify_all();

        std::this_thread::sleep_for(std::chrono::milliseconds(dis(gen)));
    }
    std::cout << "消费者 " << id << " 结束\n";
}

int main() {
    auto start = std::chrono::steady_clock::now();

    std::thread p1(producer, 1);
    std::thread p2(producer, 2);
    std::thread c1(consumer, 1);
    std::thread c2(consumer, 2);

    p1.join();
    p2.join();

    {
        std::lock_guard<std::mutex> lock(mtx);
        done = true;
    }
    cv.notify_all();

    c1.join();
    c2.join();

    auto end = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    std::cout << "\n总耗时: " << elapsed.count() << " 秒\n";

    return 0;
}
