"""Dip-buy BTC bot for make.fun btc-race-24h-20261118-1444.

Idea: one-minute BTC closes mean-revert around their recent average. The bot
waits for a real dip -- the close at least 110 basis points under its 120-bar
simple moving average -- buys everything, and gets out on whichever comes
first: the bounce reaches +150 bps above the entry close, or the price gives
back 150 bps from the best close seen since entry. One entry at most, so a
bad dip can cost at most one round trip; a late fallback buy (after bar 1000,
only if no dip ever fired and the close is above the average) guarantees the
race window still sees a trade.

Everything is integer arithmetic on closes. No clock, no network, no files,
no randomness, so two runs decide the same orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
BPS = 10_000
SMA_BARS = 120
DIP_BPS = 110
TAKE_PROFIT_BPS = 150
TRAIL_BPS = 150
MAX_SLIPPAGE_BPS = 200
FALLBACK_BAR = 1000
MAX_ENTRIES = 1


class DipBuyer:
    """Keeps the moving-average history and the entry bookkeeping."""

    def __init__(self):
        self.closes = []
        self.running_sum = 0
        self.entries = 0
        self.entry_close = None
        self.best_close = None

    def _remember(self, close):
        self.closes.append(close)
        self.running_sum += close
        if len(self.closes) > SMA_BARS:
            self.running_sum -= self.closes[-SMA_BARS - 1]

    def _average(self):
        # The average needs a full window plus one bar, so the first bar it
        # can trade on is the one after the window is complete.
        if len(self.closes) <= SMA_BARS:
            return None
        return self.running_sum // SMA_BARS

    def _buy_all(self, state):
        self.entries += 1
        close = state.close(SYMBOL)
        self.entry_close = close
        self.best_close = close
        return [{
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": state.cash,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    def _sell_all(self, state):
        holding = state.positions.get(SYMBOL)
        self.entry_close = None
        self.best_close = None
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self._remember(close)
        average = self._average()
        if average is None:
            return []

        holding = state.positions.get(SYMBOL)
        if holding is not None and holding.qty > 0:
            # Re-sync if the entry bookkeeping was lost (e.g. a rejected
            # sell): measure from the current close, never from stale data.
            if self.entry_close is None:
                self.entry_close = close
                self.best_close = close
            if close > self.best_close:
                self.best_close = close
            bounced = close * BPS >= self.entry_close * (BPS + TAKE_PROFIT_BPS)
            faded = close * BPS < self.best_close * (BPS - TRAIL_BPS)
            if bounced or faded:
                return self._sell_all(state)
            return []

        # Flat: forget any stale entry bookkeeping.
        self.entry_close = None
        self.best_close = None
        if self.entries >= MAX_ENTRIES:
            return []
        dipped = close * BPS < average * (BPS - DIP_BPS)
        if dipped:
            return self._buy_all(state)
        if (self.entries == 0 and state.seq >= FALLBACK_BAR
                and close > average):
            return self._buy_all(state)
        return []


makefun_bars.run(DipBuyer().on_batch)
