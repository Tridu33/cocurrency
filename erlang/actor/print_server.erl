%%%-------------------------------------------------------------------
%%% 范式3: Actor 模型 — 打印服务器 (gen_server)
%%%
%%% 对标 Python actor_print_server.py / Akka Typed
%%% 编译: erlc print_server.erl
%%% 运行: erl -noshell -s print_server test -s init stop
%%%-------------------------------------------------------------------
-module(print_server).
-behaviour(gen_server).

%% API
-export([start_link/0, print/2, stop/0, test/0]).

%% gen_server callbacks
-export([init/1, handle_call/3, handle_cast/2, handle_info/2, terminate/2]).

%%%===================================================================
%%% API
%%%===================================================================

start_link() ->
    gen_server:start_link({local, ?MODULE}, ?MODULE, [], []).

%% 同步请求: 打印消息并返回格式化的结果
print(Format, Args) ->
    gen_server:call(?MODULE, {print, Format, Args}).

stop() ->
    gen_server:stop(?MODULE).

%%%===================================================================
%%% gen_server callbacks
%%%===================================================================

init([]) ->
    {ok, #{counter => 0}}.

%% 同步 call: 打印并返回
handle_call({print, Format, Args}, _From, State = #{counter := Cnt}) ->
    Message = io_lib:format(Format, Args),
    io:format("[~p] ~s~n", [Cnt, lists:flatten(Message)]),
    {reply, {ok, Cnt + 1, lists:flatten(Message)}, State#{counter := Cnt + 1}}.

handle_cast(_Msg, State) ->
    {noreply, State}.

handle_info(_Info, State) ->
    {noreply, State}.

terminate(_Reason, _State) ->
    ok.

%%%===================================================================
%%% Test
%%%===================================================================

test() ->
    {ok, _Pid} = print_server:start_link(),
    {ok, N1, Msg1} = print_server:print("Hello, ~s!", ["Actor World"]),
    io:format("打印 #~p: ~s~n", [N1, Msg1]),
    {ok, N2, Msg2} = print_server:print("Count: ~p", [42]),
    io:format("打印 #~p: ~s~n", [N2, Msg2]),
    {ok, N3, Msg3} = print_server:print("Pi = ~.2f", [3.14159]),
    io:format("打印 #~p: ~s~n", [N3, Msg3]),
    ok.
