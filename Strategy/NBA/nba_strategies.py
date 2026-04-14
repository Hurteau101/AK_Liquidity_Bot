from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from Strategy.strategy import Strategy
from liqudity_context import LiquidityContext


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

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False

        matched = (
            self.is_favorite_spread(highest_order_side=liquidity_context_data.highest_order.get("side", ''))
            and self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
            and self.LOWEST_HIGHEST_ORDER <= liquidity_context_data.highest_order.get("liquidity_left") <= self.HIGHEST_HIGHEST_ORDER
            and self.LOWEST_LIQUIDITY_DIFFERENCE <= liquidity_context_data.liquidity_difference <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBASpreadSignalDecay(Strategy):
    LOWEST_HIGHEST_ORDER = 5000
    HIGHEST_HIGHEST_ORDER = 7500
    LOWEST_LIQUIDITY_DIFFERENCE = 5000
    HIGHEST_LIQUIDITY_DIFFERENCE = 15_000
    STRATEGY_COLOR = 0x8B4513


    def __init__(self):
        super().__init__(strategy_type="Signal Decay")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False

        matched = (
            self.LOWEST_HIGHEST_ORDER <= liquidity_context_data.highest_order.get("liquidity_left") <= self.HIGHEST_HIGHEST_ORDER
            and self.LOWEST_LIQUIDITY_DIFFERENCE <= liquidity_context_data.liquidity_difference <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

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

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False


        matched = (
                self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
                and self.LOWEST_HIGHEST_ORDER <= liquidity_context_data.highest_order.get("liquidity_left", 0) <= self.HIGHEST_HIGHEST_ORDER
                and self.LOWEST_LIQUIDITY_DIFFERENCE <= liquidity_context_data.liquidity_difference <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True


class NBASpreadVolumeFavorites(Strategy):
    LOWEST_ODDS = -125
    HIGHEST_ODDS = 125
    LOWEST_HIGHEST_ORDER = 4800
    HIGHEST_HIGHEST_ORDER = 6000
    STRATEGY_COLOR = 0x85C1E9


    def __init__(self):
        super().__init__(strategy_type="Volume Favorites")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False

        matched = (
                self.is_favorite_spread(highest_order_side=liquidity_context_data.highest_order.get("side", ''))
                and self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
                and self.LOWEST_HIGHEST_ORDER <= liquidity_context_data.highest_order.get("liquidity_left", 0) <= self.HIGHEST_HIGHEST_ORDER
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

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

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False

        matched = (
                self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
                and self.LOWEST_HIGHEST_ORDER <= liquidity_context_data.highest_order.get("liquidity_left", 0) <= self.HIGHEST_HIGHEST_ORDER
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True


class NBASpreadValueHunter(Strategy):
    LOWEST_ODDS = 100
    HIGHEST_ODDS = 125
    LOWEST_HIGHEST_ORDER = 10_000
    STRATEGY_COLOR = 0xC75A00


    def __init__(self):
        super().__init__(strategy_type="Value Hunter")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False


        matched = (
            self.is_underdog_spread(highest_order_side=liquidity_context_data.highest_order.get("side", '-'))
            and self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
            and liquidity_context_data.highest_order.get("liquidity_left", 0) >= self.LOWEST_HIGHEST_ORDER
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBASpreadWhale(Strategy):
    LOWEST_ODDS = -140
    HIGHEST_ODDS = 140
    LOWEST_HIGHEST_ORDER = 8500
    LOWEST_LIQUIDITY_DIFFERENCE = 15000
    STRATEGY_COLOR = 0x27F554


    def __init__(self):
        super().__init__(strategy_type="Whale")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False

        matched = (
                self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
                and liquidity_context_data.highest_order.get("liquidity_left", 0) >= self.LOWEST_HIGHEST_ORDER
                and liquidity_context_data.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBASpreadGodTier(Strategy):
    LOWEST_ODDS = 100
    HIGHEST_ODDS = 140
    LOWEST_HIGHEST_ORDER = 8500
    LOWEST_LIQUIDITY_DIFFERENCE = 15000
    STRATEGY_COLOR = 0x7AF99A


    def __init__(self):
        super().__init__(strategy_type="God Tier")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "spread" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context)

        if not liquidity_context_data:
            return False


        matched = (
                self.is_favorite_spread(highest_order_side=liquidity_context_data.highest_order.get("side", ''))
                and self.LOWEST_ODDS <= liquidity_context_data.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
                and liquidity_context_data.highest_order.get("liquidity_left", 0) >= self.LOWEST_HIGHEST_ORDER
                and liquidity_context_data.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True



# ############# TOTALS ################

class NBATotalGoldUnder(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 20_000
    LOWEST_ODDS = 100
    STRATEGY_COLOR = 0xFFD700

    def __init__(self):
        super().__init__(strategy_type="Gold Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context, highest_type="highest_liquidity_difference")

        if not liquidity_context_data:
            return False

        matched = (
                "under" in liquidity_context_data.highest_order.get("side", '').lower()
                and liquidity_context_data.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
                and liquidity_context_data.highest_order.get("american_price", 0) >= self.LOWEST_ODDS
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True


class NBATotalPlatinumUnder(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 10_000
    LOWEST_LINE = 235
    STRATEGY_COLOR = 0xC75A00

    def __init__(self):
        super().__init__(strategy_type="Platinum Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context, highest_type="highest_liquidity_difference")

        if not liquidity_context_data:
            return False

        matched = (
            "under" in liquidity_context_data.highest_order.get("side", '').lower()
            and liquidity_context_data.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
            and liquidity_context_data.additional_data.get("line", 0) >= self.LOWEST_LINE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBATotalEliteOver(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 10_000
    LOWEST_LINE = 235
    LOWEST_ODDS = 100
    STRATEGY_COLOR = 0x0D0D0D

    def __init__(self):
        super().__init__(strategy_type="Elite Over")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context, highest_type="highest_liquidity_difference")

        if not liquidity_context_data:
            return False

        matched = (
                "over" in liquidity_context_data.highest_order.get("side", '').lower()
                and liquidity_context_data.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
                and liquidity_context_data.additional_data.get("line", 0) >= self.LOWEST_LINE
                and liquidity_context_data.highest_order.get("american_price", 0) >= self.LOWEST_ODDS
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBATotalSilverUnder(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 10_000
    HIGHEST_LIQUIDITY_DIFFERENCE  = 20_000
    STRATEGY_COLOR = 0xE8E8E8

    def __init__(self):
        super().__init__(strategy_type="Silver Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context, highest_type="highest_liquidity_difference")

        if not liquidity_context_data:
            return False

        matched = (
                "under" in liquidity_context_data.highest_order.get("side", '').lower()
                and self.LOWEST_LIQUIDITY_DIFFERENCE <= liquidity_context_data.liquidity_difference <= self.HIGHEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

class NBATotalTrueSilverUnder(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 10_000
    HIGHEST_LIQUIDITY_DIFFERENCE  = 20_000
    HIGHEST_LINE = 235
    MINUTES_FROM_GAME_START = 60
    STRATEGY_COLOR = 0xA9A9A9

    def __init__(self):
        super().__init__(strategy_type="True Silver Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "nba"

    def run_match_analysis(self, liquidity_context: list[LiquidityContext], strategy_bot_instance) -> bool:
        liquidity_context_data = self.get_highest_order(liquidity_contexts=liquidity_context, highest_type="highest_liquidity_difference")

        if not liquidity_context_data:
            return False

        snapshot_time = liquidity_context_data.strategy.snapshot_time
        pacific = ZoneInfo("America/Los_Angeles")
        snapshot_time_pacific = snapshot_time.astimezone(pacific)
        start_date_dt = datetime.fromisoformat(liquidity_context_data.start_date_dt)
        pacific_start_dt = start_date_dt.astimezone(pacific)
        modified_start_date_dt = pacific_start_dt - timedelta(minutes=self.MINUTES_FROM_GAME_START)

        matched = (
            "under" in liquidity_context_data.highest_order.get("side", '').lower()
            and self.LOWEST_LIQUIDITY_DIFFERENCE <= liquidity_context_data.liquidity_difference <= self.HIGHEST_LIQUIDITY_DIFFERENCE
            and liquidity_context_data.additional_data.get("line", 0) <= self.HIGHEST_LINE
            and modified_start_date_dt <= snapshot_time_pacific <= pacific_start_dt
        )

        if not matched:
            return False

        liquidity_context_data.strategy.strategy_name = self.strategy_type
        liquidity_context_data.strategy.discord_color = self.STRATEGY_COLOR
        liquidity_context_data.strategy.include_snapshot = True

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context_data)

        return True

