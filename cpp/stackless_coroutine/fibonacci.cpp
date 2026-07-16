/**
 * 范式5: Stackless 协程 — C++20 co_yield 实现 Fibonacci 生成器
 *
 * 编译: g++ -std=c++20 -fcoroutines -pthread fibonacci.cpp -o fibonacci
 * 运行: ./fibonacci
 *
 * 注: g++ 10+ 需要 -fcoroutines; clang 需要 -std=c++20 -fcoroutines-ts -stdlib=libc++
 */

#include <coroutine>
#include <exception>
#include <iostream>
#include <cstdint>

template<typename T>
struct Generator {
    struct promise_type;
    using handle_type = std::coroutine_handle<promise_type>;

    struct promise_type {
        T value_;
        std::exception_ptr exception_;

        Generator get_return_object() {
            return Generator(handle_type::from_promise(*this));
        }
        std::suspend_always initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void unhandled_exception() { exception_ = std::current_exception(); }
        template<std::convertible_to<T> From>
        std::suspend_always yield_value(From &&from) {
            value_ = std::forward<From>(from);
            return {};
        }
        void return_void() {}
    };

    handle_type h_;
    Generator(handle_type h) : h_(h) {}
    ~Generator() { h_.destroy(); }
    explicit operator bool() {
        fill();
        return !h_.done();
    }
    T operator()() {
        fill();
        full_ = false;
        return std::move(h_.promise().value_);
    }

private:
    bool full_ = false;

    void fill() {
        if (!full_) {
            h_();
            if (h_.promise().exception_)
                std::rethrow_exception(h_.promise().exception_);
            full_ = true;
        }
    }
};

Generator<uint64_t> fibonacci_sequence(unsigned n) {
    if (n == 0) co_return;
    if (n > 94)
        throw std::runtime_error("Too big Fibonacci sequence. Elements would overflow uint64_t.");

    co_yield 0;
    if (n == 1) co_return;

    co_yield 1;
    if (n == 2) co_return;

    uint64_t a = 0, b = 1;
    for (unsigned i = 2; i < n; ++i) {
        uint64_t s = a + b;
        co_yield s;
        a = b;
        b = s;
    }
}

int main() {
    try {
        auto gen = fibonacci_sequence(20);
        std::cout << "=== Stackless 协程: Fibonacci ===\n";
        for (int j = 0; gen; ++j) {
            std::cout << "fib(" << j << ") = " << gen() << '\n';
        }

        // 比较: 性能测试
        std::cout << "\n=== 性能测试: 生成 90 个 Fibonacci 数 ===\n";
        auto gen2 = fibonacci_sequence(90);
        int count = 0;
        while (gen2) {
            gen2();
            ++count;
        }
        std::cout << "成功生成 " << count << " 个 Fibonacci 数\n";

    } catch (const std::exception &ex) {
        std::cerr << "异常: " << ex.what() << '\n';
    }
    return 0;
}
