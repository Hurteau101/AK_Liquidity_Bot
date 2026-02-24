from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from Strategy.strategy import Strategy
from discord_sender import DiscordBot

class NBASpreadSniper(Strategy):
    LOWEST_ODDS = -110
    HIGHEST_ODDS = 110
    LOWEST_HIGHEST_ORDER = 5250
    HIGHEST_HIGHEST_ORDER = 7400
    LOWEST_LIQUIDITY_DIFFERENCE = 4100
    HIGHEST_LIQUIDITY_DIFFERENCE = 8350
    STRATEGY_COLOR = 0xFF0000


    def __init__(self):
        super().__init__(strategy_type="Sniper")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, check_favourite=True)

        matched = (
            metrics["is_favorite"]
            and self.LOWEST_ODDS <= metrics["odds"] <= self.HIGHEST_ODDS
            and self.LOWEST_HIGHEST_ORDER <= metrics["highest_order_liquidity"] <= self.HIGHEST_HIGHEST_ORDER
            and self.LOWEST_LIQUIDITY_DIFFERENCE <= metrics["liquidity_difference"] <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="spread"
        )

        return True


class NBASpreadExecutive(Strategy):
    LOWEST_ODDS = -110
    HIGHEST_ODDS = 110
    LOWEST_HIGHEST_ORDER = 5000
    HIGHEST_HIGHEST_ORDER = 7500
    LOWEST_LIQUIDITY_DIFFERENCE = 4000
    HIGHEST_LIQUIDITY_DIFFERENCE = 8500
    STRATEGY_COLOR = 0x5D3A9B


    def __init__(self):
        super().__init__(strategy_type="Executive")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches)

        matched = (
                self.LOWEST_ODDS <= metrics["odds"] <= self.HIGHEST_ODDS
                and self.LOWEST_HIGHEST_ORDER <= metrics["highest_order_liquidity"] <= self.HIGHEST_HIGHEST_ORDER
                and self.LOWEST_LIQUIDITY_DIFFERENCE <= metrics["liquidity_difference"] <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="spread"
        )

        return True

class NBASpreadVolume(Strategy):
    LOWEST_ODDS = -125
    HIGHEST_ODDS = 125
    LOWEST_HIGHEST_ORDER = 4800
    HIGHEST_HIGHEST_ORDER = 6000
    STRATEGY_COLOR = 0x3498DB


    def __init__(self):
        super().__init__(strategy_type="Volume")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches)

        matched = (
                self.LOWEST_ODDS <= metrics["odds"] <= self.HIGHEST_ODDS
                and self.LOWEST_HIGHEST_ORDER <= metrics["liquidity_difference"] <= self.HIGHEST_HIGHEST_ORDER
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="spread"
        )

        return True

class NBASpreadWhale(Strategy):
    LOWEST_ODDS = -40
    HIGHEST_ODDS = 140
    LOWEST_HIGHEST_ORDER = 8500
    LOWEST_LIQUIDITY_DIFFERENCE = 15000
    STRATEGY_COLOR = 0x27F554


    def __init__(self):
        super().__init__(strategy_type="Whale")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches)

        matched = (
                self.LOWEST_ODDS <= metrics["odds"] <= self.HIGHEST_ODDS
                and metrics["highest_order_liquidity"] >= self.LOWEST_HIGHEST_ORDER
                and metrics["liquidity_difference"] >= self.LOWEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="spread"
        )

        return True

class NBATotalGoldUnder(Strategy):
    TOTAL_UNDER_LIQUIDITY = 20_000
    LOWEST_ODDS = 100
    STRATEGY_COLOR = 0xFFD700

    def __init__(self):
        super().__init__(strategy_type="Gold Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")

        matched = (
            metrics["total_under_liquidity"] >= self.TOTAL_UNDER_LIQUIDITY
            and metrics["odds"] >= self.LOWEST_ODDS
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True

class NBATotalPlatinumUnder(Strategy):
    TOTAL_UNDER_LIQUIDITY = 10_000
    LOWEST_LINE = 235
    STRATEGY_COLOR = 0xC75A00

    def __init__(self):
        super().__init__(strategy_type="Platinum Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")

        matched = (
            metrics["total_under_liquidity"] >= self.TOTAL_UNDER_LIQUIDITY
            and metrics["line"] >= self.LOWEST_LINE
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True

class NBATotalEliteOver(Strategy):
    TOTAL_OVER_LIQUIDITY = 10_000
    LOWEST_LINE = 235
    LOWEST_ODDS = 100
    STRATEGY_COLOR = 0x0D0D0D

    def __init__(self):
        super().__init__(strategy_type="Elite Over")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")

        matched = (
            metrics["total_over_liquidity"] >= self.TOTAL_OVER_LIQUIDITY
            and metrics["line"] >= self.LOWEST_LINE
            and metrics["odds"] >= self.LOWEST_ODDS
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True

class NBATotalSilverUnder(Strategy):
    LOWEST_TOTAL_OVER_LIQUIDITY = 10_000
    HIGHEST_TOTAL_OVER_LIQUIDITY = 20_000
    STRATEGY_COLOR = 0xE8E8E8

    def __init__(self):
        super().__init__(strategy_type="Silver Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")

        matched = (
            self.LOWEST_TOTAL_OVER_LIQUIDITY <= metrics["total_under_liquidity"] <= self.HIGHEST_TOTAL_OVER_LIQUIDITY
        )

        if not matched:
            return False

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True

class NBATotalTrueSilverUnder(Strategy):
    HIGHEST_LINE = 235
    MINUTES_FROM_GAME_START = 60
    STRATEGY_COLOR = 0xA9A9A9
    
    def __init__(self):
        super().__init__(strategy_type="True Silver Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")

        snapshot_time = metrics.get("snapshot_time")
        pacific = ZoneInfo("America/Los_Angeles")
        snapshot_time_pacific = snapshot_time.astimezone(pacific)
        start_date_dt = datetime.fromisoformat(start_date)
        pacific_start_dt = start_date_dt.astimezone(pacific)

        modified_start_date_dt = pacific_start_dt - timedelta(minutes=self.MINUTES_FROM_GAME_START)

        matched = (
            metrics["line"] <= self.HIGHEST_LINE
            and modified_start_date_dt <= snapshot_time_pacific <= pacific_start_dt
        )

        if not matched:
            return False

        order.update({"pacific_snapshot": snapshot_time})

        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True
