import os
from datetime import datetime, timezone

from discordwebhook import Discord
from dotenv import load_dotenv
from discord_sender import DiscordBot

class StrategyDiscordBot:
    load_dotenv()
    def __init__(self):
        load_dotenv()
        webhook_url = os.getenv("STRATEGY_BOT_WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("Please set STRATEGY_BOT_WEBHOOK_URL")

        self.discord = Discord(url=webhook_url)


    def discord_message(self, order_details: dict, strategy_type: str, game_time: str, strategy_color: int, stat_type: str):
        game_start_time = DiscordBot.get_time_pacific(game_start=game_time)

        stat_type = stat_type.lower()

        selections = {
            "spread": self.create_spread_message,
            "total": self.create_total_message
        }

        notification = selections.get(stat_type)(order_details=order_details, game_time=game_start_time, discord_color=strategy_color,
                                                 strategy_type=strategy_type)

        self.discord.post(embeds=[notification])


    def _create_heading(self, order_details: dict, game_time: str):
        return [
            {
                "name": "",
                "value": f"**Stat Type:** {order_details.get('stat_type')}\n",
                "inline": False
            },
            {
                "name": "Game Details",
                "value": f"**Event:**  {order_details.get('game_title')}\n"
                         f"**League:**  {order_details.get('league')}\n"
                         f"**Date:** {game_time}\n",
            }
        ]

    def _create_links(self, link_1_name: str, link_2_name: str, outcome_id_1: str, outcome_id_2: str):
        return {
            link_1_name: {
                "desktop_link": f"https://app.novig.us/events/{outcome_id_1}",
                "mobile_link": f"https://novig.onelink.me/JHQQ/events/{outcome_id_1}"
            },
            link_2_name: {
                "desktop_link": f"https://app.novig.us/events/{outcome_id_2}",
                "mobile_link": f"https://novig.onelink.me/JHQQ/events/{outcome_id_2}"
            }
        }

    def create_message(self, fields: list, discord_color: int, strategy_type: str):
        return {
            "title": strategy_type.title(),
            "color": discord_color,
            "author": {"name": "Strategy Bot"},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def create_total_message(self, order_details: dict, game_time: str, discord_color: int, strategy_type):
        fields = []
        fields.extend(self._create_heading(order_details, game_time))

        snapshot_time = order_details.get('pacific_snapshot') if order_details.get('pacific_snapshot') else None
        if snapshot_time:
            snapshot_time = snapshot_time.strftime("%H:%M")

        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{order_details.get('spread_team_1_name')}: ${order_details.get('spread_team_1_total_liquidity', 'N/A')} \n"
                     f"\n{order_details.get('spread_team_2_name')}: ${order_details.get('spread_team_2_total_liquidity', 'N/A')} \n\n"
                     f"Highest Order: ${order_details.get('liquidity_highest_order', 0)} [{order_details.get('highest_order_side', 'N/A')}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(order_details.get('odds_highest_order', 0))}\n\n"
                     f"Liquidity Difference: ${order_details.get('liquidity_difference')}\n\n"
                     f"{f'Snapshot Time: {snapshot_time} \\n' if snapshot_time else ''}```",
        })

        link_data = self._create_links(
            link_1_name=f"Over {order_details.get('line')}",
            link_2_name=f"Under {order_details.get('line')}",
            outcome_id_1=order_details.get('over_outcome_id'),
            outcome_id_2=order_details.get('under_outcome_id')
        )

        fields.extend(
            {
                "name": f"{name} Link",
                "value": f"**↠** [Mobile]({link_data.get('mobile_link')}) | [Desktop]({link_data.get('desktop_link')})",
                "inline": False
            }
            for name, link_data in link_data.items()
        )

        return self.create_message(fields, discord_color, strategy_type=strategy_type)

    def create_spread_message(self, order_details: dict, game_time: str, discord_color: int, strategy_type):
        fields = []
        fields.extend(self._create_heading(order_details, game_time))

        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{order_details.get('spread_team_1_name')}: ${order_details.get('spread_team_1_total_liquidity', 'N/A')} \n"
                     f"\n{order_details.get('spread_team_2_name')}: ${order_details.get('spread_team_2_total_liquidity', 'N/A')} \n\n"
                     f"Highest Order: ${order_details.get('liquidity_highest_order', 0)} [{order_details.get('highest_order_side', 'N/A')}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(order_details.get('odds_highest_order', 0))}\n\n"
                     f"Liquidity Difference: ${order_details.get('liquidity_difference')}\n```",
            "inline": False
        })

        link_data = self._create_links(
            link_1_name=order_details.get('spread_team_1_name'),
            link_2_name=order_details.get('spread_team_2_name'),
            outcome_id_1=order_details.get('spread_team_1_outcome_id'),
            outcome_id_2=order_details.get('spread_team_2_outcome_id')
        )

        fields.extend(
            {
                "name": f"{name} Link",
                "value": f"**↠** [Mobile]({link_data.get('mobile_link')}) | [Desktop]({link_data.get('desktop_link')})",
                "inline": False
            }
            for name, link_data in link_data.items()
        )


        return self.create_message(fields, discord_color, strategy_type=strategy_type)

