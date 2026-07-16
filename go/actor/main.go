// 范式3: Actor 模型 (CSP 模拟) — Go 打印服务器
//
// Go 没有内建的 Actor 框架, 但可以用 goroutine + channel 实现 Actor 模式
// 每个 Actor 是一个 goroutine, 通过 channel 接收消息 (mailbox)
//
// 对标: Python actor_print_server.py / Erlang gen_server
package main

import (
	"fmt"
	"sync"
)

// Message 定义了 actor 的消息格式
type Message struct {
	Content  string
	ReplyTo  chan string
}

// printServerActor 是打印服务器的 Actor 主循环
func printServerActor(inbox <-chan Message, wg *sync.WaitGroup) {
	defer wg.Done()
	counter := 0
	for msg := range inbox {
		counter++
		reply := fmt.Sprintf("[%d] 打印: %s", counter, msg.Content)
		fmt.Println(reply)
		if msg.ReplyTo != nil {
			msg.ReplyTo <- reply
		}
	}
	fmt.Println("打印服务器关闭")
}

func main() {
	fmt.Println("=== Actor 模型 (CSP 模拟) — 打印服务器 ===\n")

	inbox := make(chan Message, 100)
	var wg sync.WaitGroup

	// 启动 Actor (与 Erlang gen_server 类似)
	wg.Add(1)
	go printServerActor(inbox, &wg)

	// 发送消息给 Actor
	messages := []string{
		"Hello, Actor World!",
		"从 Go 到 Erlang 的问候",
		"Actor 模型 = 独立状态 + 消息通信",
		"对比 Erlang gen_server / Akka Typed",
	}

	for _, m := range messages {
		replyCh := make(chan string)
		inbox <- Message{Content: m, ReplyTo: replyCh}
		reply := <-replyCh
		fmt.Printf("  收到回复: %s\n", reply)
	}

	close(inbox)
	wg.Wait()

	fmt.Println("\n=== 与 Python actor_print_server.py 对比 ===")
	fmt.Println("Go:   goroutine + channel (CSP 模拟 Actor)")
	fmt.Println("Erlang: gen_server (原生 Actor)")
	fmt.Println("Python: queue.Queue + 独立线程")
	fmt.Println("Scala:  Akka Typed Actor")
	fmt.Println("三者的核心思想都是: 封装状态 + 消息通信")
}
