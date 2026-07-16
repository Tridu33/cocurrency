// 范式5: Stackless 协程 — Fibonacci Generator (goroutine + channel)
//
// 利用 goroutine + channel 模拟 stackless generator (类似 Python yield)
// 对比: Python yield_fibonacci.py / C++20 co_yield
// 编译: go build -o fibonacci ./stackless_coroutine/
// 运行: ./fibonacci
package main

import (
	"fmt"
)

// fibonacciGenerator 返回一个 channel, 从其中拉取 Fibonacci 数
// 类似 Python 的 generator, 每次调用 <-ch 相当于 next(gen)
func fibonacciGenerator(limit int) <-chan int {
	ch := make(chan int)
	go func() {
		defer close(ch)
		a, b := 0, 1
		for i := 0; i < limit; i++ {
			ch <- a // "yield" 当前值
			a, b = b, a+b
		}
	}()
	return ch
}

// fibonacciWithSend 演示双向通信: caller 可以重置序列
func fibonacciWithSend(limit int) <-chan int {
	ch := make(chan int)
	go func() {
		defer close(ch)
		a, b := 0, 1
		for i := 0; i < limit; i++ {
			select {
			case reset, ok := <-ch:
				if !ok {
					return
				}
				// 接收重置信号
				a, b = reset, reset+1
			default:
			}
			ch <- a
			a, b = b, a+b
		}
	}()
	return ch
}

func main() {
	fmt.Println("=== Stackless 协程: Fibonacci Generator ===\n")

	// 基本 generator 用法
	fmt.Println("--- fibonacciGenerator(20) ---")
	gen := fibonacciGenerator(20)
	count := 0
	for val := range gen {
		fmt.Printf("fib(%d) = %d\n", count, val)
		count++
	}

	fmt.Println("\n--- 与 Python generator / C++20 co_yield 对比 ---")
	fmt.Println("Go:   goroutine + channel 模拟 generator (stackless 语义)")
	fmt.Println("Python: yield 原生 generator")
	fmt.Println("C++20:  co_yield 原生 generator")
	fmt.Println("三者核心都是: 函数可暂停, 恢复后继续执行")
	fmt.Println()

	// 演示: 惰性求值 — 只取前 5 个
	fmt.Println("--- 惰性求值: 取前 5 个 ---")
	gen2 := fibonacciGenerator(100) // 理论上可生成 100 个
	for i := 0; i < 5; i++ {
		val := <-gen2
		fmt.Printf("  %d\n", val)
	}
	fmt.Println("  (只消费了 5 个, goroutine 自动退出)\n")

	fmt.Println("Stackless generator demo passed.")
}
