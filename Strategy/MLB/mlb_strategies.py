from Strategy.strategy import Strategy
from liqudity_context import LiquidityContext


class MLBStrikeoutGolden(Strategy):
    LOWEST_LIQUIDITY_DIFFERENCE = 2731
    STRATEGY_COLOR = 0xFFD700

    def __init__(self):
        super().__init__(strategy_type="The Golden Play")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "pitcher strikeouts" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            self.is_favorite_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
            and liquidity_context.liquidity_difference > self.LOWEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR
        liquidity_context.strategy.player_name = liquidity_context.additional_data.get("player_name", None)

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class MLBStrikeoutLowLines(Strategy):
    LOWEST_LINE = 3.5
    STRATEGY_COLOR = 0xFF1493

    def __init__(self):
        super().__init__(strategy_type="Low Line Over")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "pitcher strikeouts" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            "over" in liquidity_context.highest_order.get("side", '').lower()
            and liquidity_context.additional_data.get("line", 0) <= self.LOWEST_LINE
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR
        liquidity_context.strategy.player_name = liquidity_context.additional_data.get("player_name", None)

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True

class MLBStrikeoutFavoriteOvers(Strategy):
    STRATEGY_COLOR = 0x2F2F2F

    def __init__(self):
        super().__init__(strategy_type="Favorite Over")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "pitcher strikeouts" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            "over" in liquidity_context.highest_order.get("side", '').lower()
            and self.is_favorite_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR
        liquidity_context.strategy.player_name = liquidity_context.additional_data.get("player_name", None)

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True

class MLBStrikeoutMidLine(Strategy):
    STRATEGY_COLOR = 0xC75A00

    def __init__(self):
        super().__init__(strategy_type="Mid Line Under")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "pitcher strikeouts" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            "under" in liquidity_context.highest_order.get("side", '').lower()
            and (liquidity_context.additional_data.get("line", 0) == 4.5 or liquidity_context.additional_data.get("line", 0) == 5.5)
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR
        liquidity_context.strategy.player_name = liquidity_context.additional_data.get("player_name", None)

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True