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

    def discord_message(self, order_details: dict, strategy_type: str, game_time: str):
        game_start_time = DiscordBot.get_time_pacific(game_start=game_time)

        notification = self.create_strategy_notification(order_details=order_details, strategy_type=strategy_type, game_time=game_start_time)

        self.discord.post(embeds=[notification])

    def create_strategy_notification(self, order_details: dict, strategy_type: str, game_time: str):

        fields = []

        link_data = {
            order_details.get('spread_team_1_name'): {
                "desktop_link": f"https://app.novig.us/events/{order_details.get('spread_team_1_outcome_id')}",
                "mobile_link": f"https://novig.onelink.me/JHQQ/events/{order_details.get('spread_team_1_outcome_id')}"
            },
            order_details.get('spread_team_2_name'): {
                "desktop_link": f"https://app.novig.us/events/{order_details.get('spread_team_2_outcome_id')}",
                "mobile_link": f"https://novig.onelink.me/JHQQ/events/{order_details.get('spread_team_2_outcome_id')}"
            }
        }

        fields.append({
            "name": "",
            "value": f"**Stat Type:** {order_details.get('stat_type')}\n",
            "inline": False
        })

        fields.append({
            "name": "Game Details",
            "value": f"**Event:**  {order_details.get('game_title')}\n"
                     f"**Date:** {game_time}\n",
        })

        # Liquidity summary depends on stat_type
        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{order_details.get('spread_team_1_name')}: ${order_details.get('spread_team_1_total_liquidity', 0)} \n"
                     # f"\nCost Avg Odds: {DiscordBot.format_odds(side_1_data.get('cost_avg_odds', 0))}\n\n"
                     f"\n{order_details.get('spread_team_2_name')}: ${order_details.get('spread_team_2_total_liquidity', 0)} \n\n"
                     # f"\nCost Avg Odds: {DiscordBot.format_odds(side_2_data.get('cost_avg_odds', 0))}\n\n"
                     f"Highest Order: ${order_details.get('liquidity_highest_order', 0)} [{order_details.get('highest_order_side')}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(order_details.get('odds_highest_order', 0))}\n\n"
                     f"Liquidity Difference: ${order_details.get('liquidity_difference')}\n```",
            "inline": False
        })


        link_fields = [
            {
                "name": f"{side} Link",
                "value": f"**↠** [Mobile]({link_data.get('mobile_link')}) | [Desktop]({link_data.get('desktop_link')})",
                "inline": False
            }
            for side, link_data in link_data.items()
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
