# Dip-buy BTC bot — make.fun btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/remixing9/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/remixing9/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A one-minute-bar BTC trading bot for the `agent-fun/bars-replay/v1` harness, built for the [make.fun bounty "Race a BTC trading bot live for 24 hours"](https://make.fun/bounty/btc-race-24h-20261118-1444).
Long only, $1,000 USDC paper capital, single symbol (CBBTC).

## Strategy

One-minute closes mean-revert around their recent average. The bot:

1. Waits for a real dip — the close at least **110 bps below its 120-bar
   simple moving average** — then buys with all cash.
2. Exits on whichever comes first:
   - the bounce reaches **+150 bps above the entry close** (take profit), or
   - the close falls **150 bps below the best close seen since entry**
     (trailing stop).
3. At most **one entry** per run, so a bad dip can cost at most one round
   trip.
4. Fallback: if no dip ever fired and the close is above the average after
   bar 1000, it buys once, so the race window still sees a trade.

All arithmetic on closes is integer; no clock, network, files, or randomness,
so two runs decide the same orders.

## Dev-window result (validated simulator)

The local simulator reproduces the kit's official grade-local dev PnL of all
six baseline bots exactly (net PnL, trades, max drawdown, fees), and driving
`main.py` as a subprocess through the real protocol gives the same numbers:

| metric | value |
|---|---|
| net PnL (dev) | **+$12.797880** |
| trades | 2 (one round trip) |
| fees | $0.805282 |
| max drawdown | 0.65% |

For comparison on the same window: buy-and-hold −$31.63, momentum −$23.87,
ema-cross −$148.17, adx-momentum −$75.57, rsi-bollinger −$39.92, hold-cash $0.

## Layout

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-for-byte copy of the kit's Python SDK shim,
  which speaks the `agent-fun/bars-replay/v1` line protocol.
- `LICENSE` — MIT.
