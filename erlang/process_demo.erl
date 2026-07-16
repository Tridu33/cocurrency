%%
%% 范式6: Stackful 协程演示 — Erlang 进程 (BEAM 轻量进程)
%%
%% Erlang 进程是 BEAM 虚拟机的轻量级"绿色线程"，
%% 每个进程有独立堆栈，由 BEAM 调度器 M:N 调度到 OS 线程上。
%% 与 Lua coroutine 和 Go goroutine 类似，属于 stackful 并发单元。
%%
%% 编译: erlc process_demo.erl
%% 运行: erl -noshell -s process_demo test -s init stop
%%
-module(process_demo).
-export([fib/1, test/0]).

%% 在独立进程中启动 Fibonacci 计算
fib(N) ->
    Self = self(),
    spawn(fun() ->
        Result = fib_calc(N),
        Self ! {fib_result, N, Result}
    end).

fib_calc(0) -> 0;
fib_calc(1) -> 1;
fib_calc(N) when N > 1 -> fib_calc(N - 1) + fib_calc(N - 2).

%% 并发计算多个 Fibonacci
test() ->
    io:format("=== Erlang 进程 (Stackful 协程) 演示 ===~n"),
    io:format("每个 fib(N) 在一个独立 BEAM 进程中执行~n~n"),

    lists:foreach(fun(N) -> fib(N) end, lists:seq(0, 15)),

    collect_results(16, []).

collect_results(0, Results) ->
    Sorted = lists:sort(fun({_, A, _}, {_, B, _}) -> A =< B end, Results),
    lists:foreach(fun({fib_result, N, V}) ->
        io:format("fib(~p) = ~p~n", [N, V])
    end, Sorted);
collect_results(N, Acc) ->
    receive
        Msg = {fib_result, _, _} ->
            collect_results(N - 1, [Msg | Acc])
    end.
