%%%-------------------------------------------------------------------
%%% 范式3: Actor 模型 — 银行账户 (gen_server)
%%%
%%% 演示: 每个账户是一个独立 Actor, 消息串行处理保证一致性
%%% 编译: erlc bank_account.erl && erlc print_server.erl
%%% 运行: erl -noshell -s bank_account test -s init stop
%%%-------------------------------------------------------------------
-module(bank_account).
-behaviour(gen_server).

%% API
-export([start_link/1, balance/1, deposit/2, withdraw/2, transfer/3, stop/1, test/0]).

%% gen_server callbacks
-export([init/1, handle_call/3, handle_cast/2, handle_info/2, terminate/2]).

%%%===================================================================
%%% API
%%%===================================================================

start_link(InitialBalance) ->
    gen_server:start_link(?MODULE, [InitialBalance], []).

balance(Pid) ->
    gen_server:call(Pid, balance).

deposit(Pid, Amount) ->
    gen_server:call(Pid, {deposit, Amount}).

withdraw(Pid, Amount) ->
    gen_server:call(Pid, {withdraw, Amount}).

transfer(FromPid, ToPid, Amount) ->
    case gen_server:call(FromPid, {withdraw, Amount}) of
        {ok, NewFromBal} ->
            {ok, NewToBal} = gen_server:call(ToPid, {deposit, Amount}),
            {ok, NewFromBal, NewToBal};
        {error, Reason} ->
            {error, Reason}
    end.

stop(Pid) ->
    gen_server:stop(Pid).

%%%===================================================================
%%% gen_server callbacks
%%%===================================================================

init([InitialBalance]) when InitialBalance >= 0 ->
    {ok, InitialBalance}.

handle_call(balance, _From, Balance) ->
    {reply, {ok, Balance}, Balance};

handle_call({deposit, Amount}, _From, Balance) when Amount > 0 ->
    NewBalance = Balance + Amount,
    io:format("存款 ~p, 余额: ~p -> ~p~n", [Amount, Balance, NewBalance]),
    {reply, {ok, NewBalance}, NewBalance};

handle_call({withdraw, Amount}, _From, Balance) when Amount > 0, Amount =< Balance ->
    NewBalance = Balance - Amount,
    io:format("取款 ~p, 余额: ~p -> ~p~n", [Amount, Balance, NewBalance]),
    {reply, {ok, NewBalance}, NewBalance};

handle_call({withdraw, Amount}, _From, Balance) ->
    {reply, {error, insufficient_funds}, Balance};

handle_call(_Request, _From, State) ->
    {reply, {error, unknown_request}, State}.

handle_cast(_Msg, State) -> {noreply, State}.
handle_info(_Info, State) -> {noreply, State}.
terminate(_Reason, _State) -> ok.

%%%===================================================================
%%% Test
%%%===================================================================

test() ->
    {ok, Acc1} = bank_account:start_link(1000),
    {ok, Acc2} = bank_account:start_link(500),

    {ok, B1} = bank_account:balance(Acc1),
    {ok, B2} = bank_account:balance(Acc2),
    io:format("初始余额: 账户1 = ~p, 账户2 = ~p~n", [B1, B2]),

    {ok, NB1} = bank_account:deposit(Acc1, 200),
    io:format("存款后余额: ~p~n", [NB1]),

    {ok, NB2} = bank_account:withdraw(Acc2, 100),
    io:format("取款后余额: ~p~n", [NB2]),

    case bank_account:transfer(Acc1, Acc2, 300) of
        {ok, FBal1, FBal2} ->
            io:format("转账 300 成功: 账户1 = ~p, 账户2 = ~p~n", [FBal1, FBal2]);
        {error, Reason} ->
            io:format("转账失败: ~p~n", [Reason])
    end,

    %% 测试余额不足
    case bank_account:withdraw(Acc1, 99999) of
        {ok, _} -> ok;
        {error, insufficient_funds} ->
            io:format("余额不足检查正确~n")
    end,

    bank_account:stop(Acc1),
    bank_account:stop(Acc2),
    ok.
