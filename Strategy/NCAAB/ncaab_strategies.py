from dataclasses import asdict

from Strategy.strategy import Strategy
from liqudity_context import LiquidityContext, LiquidityStrategy


class NCAABTotalSkyHigh(Strategy):
    LOWEST_LINE = 160
    STRATEGY_COLOR = 0x1E90FF

    def __init__(self):
        super().__init__(strategy_type="Sky High Total")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.highest_order.get("side", '') == "over"
            and liquidity_context.additional_data.get("line", 0) > self.LOWEST_LINE
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True

class NCAABTotalUnder(Strategy):
    HIGHEST_LINE = 150
    LOWEST_ODDS = -105
    HIGHEST_ODDS = 105
    STRATEGY_COLOR = 0xFF1493

    def __init__(self):
        super().__init__(strategy_type="Under Strategy")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.highest_order.get("side", '') == "under"
            and liquidity_context.additional_data.get("line", 0) < self.HIGHEST_LINE
            and self.LOWEST_ODDS < liquidity_context.highest_order.get("american_price", 0) < self.HIGHEST_ODDS
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True

class NCAABTotalGoldMine(Strategy):
    HIGHEST_LINE = 150
    LOWEST_ODDS = -105
    HIGHEST_ODDS = 100
    STRATEGY_COLOR = 0xFFD700

    def __init__(self):
        super().__init__(strategy_type="Gold Mine")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.additional_data.get("line", 0) <= self.HIGHEST_LINE
            and self.LOWEST_ODDS <= liquidity_context.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class NCAABTotalLowLine(Strategy):
    HIGHEST_LINE = 140
    STRATEGY_COLOR = 0x2F2F2F

    def __init__(self):
        super().__init__(strategy_type="Low Lines")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.additional_data.get("line", 0) < self.HIGHEST_LINE
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class NCAABTotalOverHighJuice(Strategy):
    HIGHEST_ODDS = -111
    STRATEGY_COLOR = 0x800080

    def __init__(self):
        super().__init__(strategy_type="Over High Juice")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.highest_order.get("side", '') == "over"
            and liquidity_context.highest_order.get("american_price", 0) <= self.HIGHEST_ODDS
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True