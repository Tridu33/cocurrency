%%%-------------------------------------------------------------------
%%% 范式2: CSP — Channel 通信 (进程 + 消息传递)
%%%
%%% Erlang 没有内建 Channel, 但可以用进程 + selective receive
%%% 实现 CSP 风格的同步通信
%%%
%%% 对标: Go channel / Python channel_demo.py
%%% 编译: erlc channel_demo.erl
%%% 运行: erl -noshell -s channel_demo test -s init stop
%%%-------------------------------------------------------------------
-module(channel_demo).
-export([test/0, channel/0, producer/2, consumer/2]).

%%%===================================================================
%%% Channel 进程
%%%===================================================================

%% channel 服务器: 维护一个队列和等待队列
channel() ->
    channel_loop([]).

channel_loop(Buffer) ->
    receive
        {send, Value, From} ->
            NewBuf = Buffer ++ [Value],
            io:format("  [ch] send ~p (buf_size=~p)~n", [Value, length(NewBuf)]),
            From ! {ok, self()},
            channel_loop(NewBuf);

        {recv, From} ->
            case Buffer of
                [Value | Rest] ->
                    io:format("  [ch] recv ~p (buf_size=~p)~n", [Value, length(Rest)]),
                    From ! {value, Value, self()},
                    channel_loop(Rest);
                [] ->
                    %% 缓冲区空, 等待发送者
                    receive
                        {send, NewValue, Sender} ->
                            io:format("  [ch] send ~p -> 直接传递给等待的 recv~n", [NewValue]),
                            Sender ! {ok, self()},
                            From ! {value, NewValue, self()},
                            channel_loop([])
                    end
            end;

        {close, _From} ->
            io:format("  [ch] channel closed~n"),
            channel_loop(closed)
    end.

%%%===================================================================
%%% 生产者
%%%===================================================================

producer(ChPid, Values) ->
    lists:foreach(fun(V) ->
        ChPid ! {send, V, self()},
        receive
            {ok, _} -> ok
        end
    end, Values),
    io:format("  [producer] all values sent~n").

%%%===================================================================
%%% 消费者
%%%===================================================================

consumer(ChPid, Count) ->
    consumer_loop(ChPid, Count, []).

consumer_loop(_ChPid, 0, Acc) ->
    io:format("  [consumer] received ~p values~n", [length(Acc)]),
    Acc;
consumer_loop(ChPid, N, Acc) ->
    ChPid ! {recv, self()},
    receive
        {value, V, _} ->
            io:format("  [consumer] got ~p~n", [V]),
            consumer_loop(ChPid, N - 1, [V | Acc])
    end.

%%%===================================================================
%%% 测试
%%%===================================================================

test() ->
    io:format("=== CSP Channel Demo (Erlang 进程模拟) ===~n~n"),

    %% Demo 1: 无缓冲通道
    io:format("--- Demo 1: 无缓冲通道 ---~n"),
    ChPid1 = spawn(fun channel/0),
    Producer1 = spawn(fun() -> producer(ChPid1, [10, 20, 30, 40, 50]) end),
    Consumer1 = spawn(fun() -> consumer(ChPid1, 5) end),
    timer:sleep(200),
    io:format("~n"),

    %% Demo 2: 多生产者 - 多消费者
    io:format("--- Demo 2: 双生产者 - 双消费者 ---~n"),
    ChPid2 = spawn(fun channel/0),

    spawn(fun() -> producer(ChPid2, [1, 2, 3, 4, 5]) end),
    spawn(fun() -> producer(ChPid2, [101, 102, 103, 104, 105]) end),
    spawn(fun() -> consumer(ChPid2, 5) end),
    spawn(fun() -> consumer(ChPid2, 5) end),

    timer:sleep(500),

    io:format("~n--- 与 Go channel / Python channel_demo.py 对比 ---~n"),
    io:format("Go:     goroutine + channel (原生 CSP)~n"),
    io:format("Python: queue.Queue + 自定义 Channel 类~n"),
    io:format("Erlang: 进程 + 消息传递 (模拟 channel 语义)~n"),
    io:format("三者核心都是: 通过消息传递通信, 不共享状态~n"),
    ok.
