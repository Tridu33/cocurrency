// 范式2: CSP (通信顺序进程) — Go channel 深度演示
//
// 包含 4 个 channel demo:
// 1. 基本 channel: 无缓冲 producer-consumer
// 2. 带缓冲 channel: 异步生产消费
// 3. select 多路复用: 同时监听多个 channel
// 4. pipeline: channel 连接多个 goroutine
package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// --------------------------------------------------------------------------
// Demo 1: 无缓冲 channel — 同步生产者消费者
// --------------------------------------------------------------------------
func demo1() {
	fmt.Println("=== Demo 1: 无缓冲 Channel (同步 CSP) ===")
	ch := make(chan int)

	go func() {
		for i := 0; i < 5; i++ {
			msg := i * 10
			fmt.Printf("  生产者发送: %d\n", msg)
			ch <- msg // 阻塞直到消费者接收
		}
		close(ch)
	}()

	for val := range ch {
		fmt.Printf("  消费者接收: %d\n", val)
		time.Sleep(50 * time.Millisecond)
	}
	fmt.Println()
}

// --------------------------------------------------------------------------
// Demo 2: 带缓冲 channel — 异步生产者消费者
// --------------------------------------------------------------------------
func demo2() {
	fmt.Println("=== Demo 2: 缓冲 Channel (异步 CSP) ===")
	ch := make(chan int, 3)
	var wg sync.WaitGroup

	// 生产者: 快速生产
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < 6; i++ {
			ch <- i
			fmt.Printf("  生产: %d (缓冲: %d/%d)\n", i, len(ch), cap(ch))
		}
		close(ch)
	}()

	// 消费者: 慢速消费
	wg.Add(1)
	go func() {
		defer wg.Done()
		for val := range ch {
			fmt.Printf("  消费: %d\n", val)
			time.Sleep(100 * time.Millisecond)
		}
	}()

	wg.Wait()
	fmt.Println()
}

// --------------------------------------------------------------------------
// Demo 3: select 多路复用 — 同时监听多个 channel
// --------------------------------------------------------------------------
func demo3() {
	fmt.Println("=== Demo 3: select 多路复用 ===")
	ch1 := make(chan string)
	ch2 := make(chan string)
	done := make(chan struct{})

	// 两个生产者
	go func() {
		for i := 0; i < 3; i++ {
			time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
			ch1 <- fmt.Sprintf("来自 ch1 的消息 #%d", i)
		}
	}()
	go func() {
		for i := 0; i < 3; i++ {
			time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
			ch2 <- fmt.Sprintf("来自 ch2 的消息 #%d", i)
		}
	}()

	// 消费者: select 多路复用
	go func() {
		recv1, recv2 := 0, 0
		for recv1 < 3 || recv2 < 3 {
			select {
			case msg := <-ch1:
				fmt.Printf("  ch1: %s\n", msg)
				recv1++
			case msg := <-ch2:
				fmt.Printf("  ch2: %s\n", msg)
				recv2++
			case <-time.After(500 * time.Millisecond):
				fmt.Println("  超时!")
			}
		}
		close(done)
	}()

	<-done
	fmt.Println()
}

// --------------------------------------------------------------------------
// Demo 4: Pipeline — channel 连接多个 goroutine
// --------------------------------------------------------------------------
func generator(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		for _, n := range nums {
			out <- n
		}
		close(out)
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		for n := range in {
			out <- n * n
		}
		close(out)
	}()
	return out
}

func demo4() {
	fmt.Println("=== Demo 4: Pipeline (Channel 连接多个 Goroutine) ===")
	// 构建 pipeline: generator -> square -> 打印
	nums := []int{1, 2, 3, 4, 5, 6, 7, 8}
	for result := range square(generator(nums...)) {
		fmt.Printf("  %d^2 = %d\n", result, result)
	}
	fmt.Println()
}

func main() {
	demo1()
	demo2()
	demo3()
	demo4()
}
