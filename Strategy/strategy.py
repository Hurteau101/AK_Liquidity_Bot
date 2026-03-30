from abc import ABC, abstractmethod

from liqudity_context import LiquidityContext


class Strategy(ABC):
    def __init__(self, strategy_type: str):
        self.strategy_type = strategy_type

    # def _get_highest_order_metrics(self, liquidity_contexts: list[LiquidityContext], check_favourite: bool = False,
    #                                highest_type: str = "highest_order", check_underdog: bool = False):
    #     return self.highest_order_getter(highest_type=highest_type, liquidity_contexts=liquidity_contexts)

    @abstractmethod
    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        pass

    @abstractmethod
    def run_match_analysis(self, liquidity_context: LiquidityContext, strategy_bot_instance) -> bool:
        pass

    def is_underdog(self, highest_order_side: str):
        """Check if the highest order side indicates an underdog (e.g., does not contain a "-")"""
        return "-" not in str(highest_order_side)

    def is_favorite(self, highest_order_side: str):
        """Check if the highest order side indicates a favorite (e.g., contains a "-")"""
        return "-" in str(highest_order_side)

    def get_highest_order(self, liquidity_contexts: list[LiquidityContext],
                             highest_type: str = "highest_order") -> LiquidityContext:
        """Returns the match with the highest order or liquidity difference"""
        if highest_type not in ["highest_order", "highest_liquidity_difference"]:
            raise ValueError("highest_type must be either 'highest_order' or 'highest_liquidity_difference'")

        if highest_type == "highest_order":
            return max(liquidity_contexts, key=lambda x: x.highest_order.get("liquidity_left", 0), default=None)

        return max(liquidity_contexts, key=lambda x: x.liquidity_difference, default=None)
        # return max(matches, key=lambda x: x["liquidity_difference"], default=None)



    def send_message(self, strategy_bot_instance, liquidity_context: LiquidityContext):
        strategy_bot_instance.discord_message(liquidity_context=liquidity_context)

    # def send_message(self, strategy_bot_instance, highest_order: dict, strategy_type: str, start_date: str,
    #                  strategy_color: int, stat_type: str):
        # strategy_bot_instance.discord_message(
        #     order_details=highest_order,
        #     strategy_type=strategy_type,
        #     game_time=start_date,
        #     strategy_color=strategy_color,
        #     stat_type=stat_type
        # )

