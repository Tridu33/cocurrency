/**
 * 范式1: 共享内存 + 锁 — 死锁演示 (C++11)
 *
 * 两个线程以不同顺序加锁, 导致死锁。
 * 编译: g++ -std=c++11 -pthread deadlock.cpp -o deadlock
 * 运行: ./deadlock
 *
 * 预期输出:
 *   线程 A: 获取 mtx_a
 *   线程 B: 获取 mtx_b
 *   线程 A: 等待 mtx_b... (卡住)
 *   线程 B: 等待 mtx_a... (卡住)
 *   → 死锁! 程序不会主动结束 (需要 timeout 或 Ctrl-C)
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>

std::mutex mtx_a;
std::mutex mtx_b;

void thread_a() {
    std::cout << "线程 A: 获取 mtx_a\n";
    mtx_a.lock();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    std::cout << "线程 A: 等待 mtx_b...\n";
    mtx_b.lock();  // 死锁: B 持有 mtx_b 正等待 mtx_a
    std::cout << "线程 A: 获取 mtx_b\n";
    mtx_b.unlock();
    mtx_a.unlock();
}

void thread_b() {
    std::cout << "线程 B: 获取 mtx_b\n";
    mtx_b.lock();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    std::cout << "线程 B: 等待 mtx_a...\n";
    mtx_a.lock();  // 死锁: A 持有 mtx_a 正等待 mtx_b
    std::cout << "线程 B: 获取 mtx_a\n";
    mtx_a.unlock();
    mtx_b.unlock();
}

int main() {
    std::cout << "=== 死锁演示 ===\n"
              << "线程 A: lock(mtx_a) -> lock(mtx_b)\n"
              << "线程 B: lock(mtx_b) -> lock(mtx_a)\n"
              << "两线程互相等待 → 死锁!\n"
              << "程序将在 3 秒后自动终止 (timeout)\n\n";

    std::thread t1(thread_a);
    std::thread t2(thread_b);

    /* 修复死锁: 固定加锁顺序
     * 两个线程都以 (mtx_a, mtx_b) 顺序加锁:
     *
     * void thread_a_fixed() {
     *     std::lock_guard<std::mutex> lock_a(mtx_a);
     *     std::lock_guard<std::mutex> lock_b(mtx_b);
     *     // ... 临界区 ...
     * }
     *
     * void thread_b_fixed() {
     *     std::lock_guard<std::mutex> lock_a(mtx_a); // 注意: 先 A 再 B
     *     std::lock_guard<std::mutex> lock_b(mtx_b);
     *     // ... 临界区 ...
     * }
     */

    t1.join();
    t2.join();

    std::cout << "程序结束 (不会到达这里, 因为死锁)\n";
    return 0;
}
