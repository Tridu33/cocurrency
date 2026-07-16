// 范式1: 共享内存 + 锁 — Go Mutex + WaitGroup
//
// 演示: 多个 goroutine 通过 Mutex 安全访问共享计数器
// 编译: go build -o mutex_demo main.go
// 运行: ./mutex_demo
package main

import (
	"fmt"
	"sync"
)

type SafeCounter struct {
	mu    sync.Mutex
	value int
}

func (c *SafeCounter) Inc() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.value++
}

func (c *SafeCounter) Dec() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.value--
}

func (c *SafeCounter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.value
}

func main() {
	fmt.Println("=== 共享内存 + 锁: Mutex 保护共享计数器 ===")

	var counter SafeCounter
	var wg sync.WaitGroup

	// 10 个 goroutine 并发增加
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				counter.Inc()
			}
			fmt.Printf("  goroutine %d 完成\n", id)
		}(i)
	}

	wg.Wait()
	fmt.Printf("最终计数器值: %d (期望: %d)\n", counter.Value(), 10*1000)
	fmt.Println()

	// 演示: 死锁预防 — 固定顺序加锁
	fmt.Println("=== 死锁预防: 固定顺序加锁 ===")
	var mu1, mu2 sync.Mutex

	var wg2 sync.WaitGroup
	wg2.Add(2)

	go func() {
		defer wg2.Done()
		mu1.Lock()
		mu2.Lock()
		fmt.Println("  goroutine A 获取两把锁")
		mu2.Unlock()
		mu1.Unlock()
	}()

	go func() {
		defer wg2.Done()
		mu1.Lock() // 与 A 相同的加锁顺序 → 不会死锁
		mu2.Lock()
		fmt.Println("  goroutine B 获取两把锁")
		mu2.Unlock()
		mu1.Unlock()
	}()

	wg2.Wait()
	fmt.Println("  死锁预防成功!")
}
