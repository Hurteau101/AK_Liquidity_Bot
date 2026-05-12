from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from Strategy.strategy import Strategy
from liqudity_context import LiquidityContext


#### STRIKEOUT ####

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



##### 1ST HALF #####

class MLB1HTierOne(Strategy):
    STRATEGY_COLOR = 0xC75A00
    LOWEST_LIQUIDITY_DIFFERENCE = 4360
    MINUTES_FROM_GAME_START = 30

    def __init__(self):
        super().__init__(strategy_type="Tier 1")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "1st half total" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        start_date_dt = datetime.fromisoformat(liquidity_context.additional_data.get("game_start_time"))
        pacific = ZoneInfo("America/Los_Angeles")
        pacific_start_dt = start_date_dt.astimezone(pacific)

        modified_start_date_dt = pacific_start_dt - timedelta(minutes=self.MINUTES_FROM_GAME_START)
        current_pacific_time = datetime.now(pacific)


        matched = (
            current_pacific_time >= modified_start_date_dt
            and "under" in liquidity_context.highest_order.get("side", '').lower()
            and self.is_favorite_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
            and liquidity_context.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class MLB1HFadeGaps(Strategy):
    STRATEGY_COLOR = 0x0D0D0D
    LOWEST_LIQUIDITY_DIFFERENCE = 5900



    def __init__(self):
        super().__init__(strategy_type="Fade Massive Gaps")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "1st half total" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE and
            (
                "over" in liquidity_context.highest_order.get("side", '').lower()
                and self.is_underdog_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
            )
            or
            (
                "under" in liquidity_context.highest_order.get("side", '').lower()
                and self.is_favorite_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
            )
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class MLB1HFadeLateReach(Strategy):
    STRATEGY_COLOR = 0x7AF99A
    MINUTES_FROM_GAME_START = 30


    def __init__(self):
        super().__init__(strategy_type="Fade Late Reaches")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "1st half total" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        start_date_dt = datetime.fromisoformat(liquidity_context.additional_data.get("game_start_time"))
        pacific = ZoneInfo("America/Los_Angeles")
        pacific_start_dt = start_date_dt.astimezone(pacific)

        modified_start_date_dt = pacific_start_dt - timedelta(minutes=self.MINUTES_FROM_GAME_START)
        current_pacific_time = datetime.now(pacific)

        matched = (
            current_pacific_time >= modified_start_date_dt and
            (
                "over" in liquidity_context.highest_order.get("side", '').lower()
            )
            or
            (
                "under" in liquidity_context.highest_order.get("side", '').lower()
                and self.is_underdog_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
            )
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True


class MLB1HFadeWhales(Strategy):
    STRATEGY_COLOR = 0x27F554
    LOWEST_LIQUIDITY_DIFFERENCE = 4987

    def __init__(self):
        super().__init__(strategy_type="Fade the Whales")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "1st half total" and league == "mlb"

    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        if not liquidity_context:
            return False

        matched = (
            liquidity_context.liquidity_difference >= self.LOWEST_LIQUIDITY_DIFFERENCE
            and "over" in liquidity_context.highest_order.get("side", '').lower()
            and self.is_underdog_odds(highest_order_odds=liquidity_context.highest_order.get("american_price", 0))
        )

        if not matched:
            return False

        liquidity_context.strategy.strategy_name = self.strategy_type
        liquidity_context.strategy.discord_color = self.STRATEGY_COLOR

        self.send_message(strategy_bot_instance=strategy_bot_instance, liquidity_context=liquidity_context)

        return True