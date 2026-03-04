from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, strategy_type: str):
        self.strategy_type = strategy_type

    def _get_highest_order_metrics(self, matches: list, check_favourite: bool = False, highest_type: str = "highest_order", highest_order_side: str = None):
        order = self.highest_order_getter(highest_type=highest_type, matches=matches, highest_order_side=highest_order_side)
        if not order:
            return None, None

        metrics = {
            "odds": float(order.get("odds_highest_order", 0)),
            "highest_order_liquidity": float(order.get("liquidity_highest_order", 0)),
            "liquidity_difference": float(order.get("liquidity_difference", 0)),
            "is_favorite": "-" in str(order.get("highest_order_side", "")) if check_favourite else False,
            "total_under_liquidity": float(order.get("total_under_liquidity", 0)) if order.get("total_under_liquidity") else 0,
            "total_over_liquidity": float(order.get("total_over_liquidity", 0)) if order.get("total_over_liquidity") else 0,
            "line": order.get("line", 0),
            "snapshot_time": order.get("snapshot_time"),
        }

        return order, metrics

    @abstractmethod
    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        pass

    @abstractmethod
    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass

    def highest_order_getter(self, highest_type: str, matches: list, highest_order_side: str = None) -> dict:
        """Returns the match with the highest order or liquidity difference"""
        if highest_type not in ["highest_order", "highest_liquidity_difference"]:
            raise ValueError("highest_type must be either 'highest_order' or 'highest_liquidity_difference'")

        return max(
            matches,
            key=lambda x: x["liquidity_highest_order"]
        ) if highest_type == "highest_order" else (
            max(
                (match for match in matches if match.get("highest_order_side") == highest_order_side),
                key=lambda x: x["liquidity_difference"],
                default=None
            )
        )

    def send_message(self, strategy_bot_instance, highest_order: dict, strategy_type: str, start_date: str,
                     strategy_color: int, stat_type: str):
        strategy_bot_instance.discord_message(
            order_details=highest_order,
            strategy_type=strategy_type,
            game_time=start_date,
            strategy_color=strategy_color,
            stat_type=stat_type
        )

