import os
from datetime import datetime, timezone
from discordwebhook import Discord
from dotenv import load_dotenv
from discord_sender import DiscordBot


class StrategyDiscordBot:
    def __init__(self):
        load_dotenv()
        webhook_url = os.getenv("STRATEGY_BOT_WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("Please set STRATEGY_BOT_WEBHOOK_URL")

        self.discord = Discord(url=webhook_url)

    def discord_message(self, highest_order: dict, strategy_type: str, market_data: dict, stat_type: str, liquidity_difference: float):
        game_start_utc_str = market_data.get("additional_data").get("game_start_time")
        game_start_time = DiscordBot.get_time_pacific(game_start=game_start_utc_str)

        notification = self.create_strategy_notification(highest_order=highest_order, strategy_type=strategy_type,
                                                         market_data=market_data, stat_type=stat_type,
                                                         game_start_time=game_start_time, liquidity_difference=liquidity_difference)

        self.discord.post(embeds=[notification])

    def create_strategy_notification(self, highest_order: dict, strategy_type: str, market_data: dict, stat_type: str, game_start_time: str,
                                     liquidity_difference: float):
        fields = []

        liquidity_data = market_data.get("liquidity", {})
        sides = list(liquidity_data.keys())

        side_1_name, side_2_name = sides[0], sides[1]
        side_1_data = liquidity_data.get(side_1_name, {}).get("highest_order", {})
        side_2_data = liquidity_data.get(side_2_name, {}).get("highest_order", {})

        fields.append({
            "name": "",
            "value": f"**Stat Type:** {stat_type}",
            "inline": False
        })

        fields.append({
            "name": "Game Details",
            "value": f"**Event:**  {market_data.get('additional_data', {}).get('game_title')}\n"
                     f"**Date:** {game_start_time}\n",
        })

        # Liquidity summary depends on stat_type
        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{side_1_name.upper()}: ${side_1_data.get('total_liquidity', 0)} "
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_1_data.get('cost_avg_odds', 0))}\n\n"
                     f"{side_2_name.upper()}: ${side_2_data.get('total_liquidity', 0)}"
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_2_data.get('cost_avg_odds', 0))}\n\n"
                     f"Highest Order: ${highest_order.get('liquidity_left', 0)} [{highest_order.get('side').title()}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(highest_order.get('american_price', 0))}\n\n"
                     f"Liquidity Difference: ${liquidity_difference}\n```",
            "inline": False
        })

        link_fields = [
            {
                "name": f"{order_data.get('side').upper()} Link",
                "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
                "inline": False
            }
            for side, data in liquidity_data.items()
            if (order_data := data.get("highest_order"))
        ]

        fields.extend(link_fields)

        strategy_colors = {
            "sniper": 0xFF0000,  # red
            "executive": 0x5D3A9B,  # purple
            "volume": 0x3498DB  # blue
        }


        return {
            "title": strategy_type.title(),
            "color": strategy_colors.get(strategy_type.lower(), 0x5D3A9B),
            "author": {"name": "Strategy Bot"},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
