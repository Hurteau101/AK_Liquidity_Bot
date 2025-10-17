import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discordwebhook import Discord


class DiscordBot:
    def __init__(self, league):
        load_dotenv()
        self.webhook = self._webhook_mapper(league)
        self.discord = Discord(url=self.webhook)

    def _webhook_mapper(self, league):
        MAPPER = {
            "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL"),
            "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA"),
        }

        if league.lower() not in MAPPER:
            raise ValueError(f"League '{league}' is not supported. Supported leagues: {list(MAPPER.keys())}")

        return MAPPER.get(league.lower(), os.getenv("DISCORD_WEBHOOK_URL"))

    def discord_message(self, data, market_changed=False):
        stat_type = data.get("additional_data").get("stat_type")
        player_name = data.get("additional_data").get("player_name")
        line = data.get("additional_data").get("line")

        game_start_utc_str = data.get("additional_data").get("game_start_time")
        if game_start_utc_str:
            game_start_utc = datetime.fromisoformat(game_start_utc_str)
            eastern = ZoneInfo("America/New_York")
            game_start_eastern = game_start_utc.astimezone(eastern)
            game_start_time = game_start_eastern.strftime("%Y-%m-%d")
        else:
            game_start_time = "N/A"


        main_title = f"{player_name} {line} {stat_type}"

        notification = self.create_notification(main_title, game_start_time, data, market_changed)
        self.discord.post(embeds=[notification])

    @staticmethod
    def format_odds(value: int | float) -> str:
        if value > 0:
            return f"+{value}"
        return str(value)

    def create_notification(self, main_title, start_time, market_data, market_change):
        fields = []

        previous_message = "*(Play was sent previously but market moved +/- 1000)*\n" if market_change else ""

        over_data = market_data.get("liquidity", {}).get("over", {}).get("highest_order", {})
        under_data = market_data.get("liquidity", {}).get("under", {}).get("highest_order", {})

        highest = max(
            market_data["liquidity"].values(),
            key=lambda x: x["highest_order"]["total_liquidity"]
        )["highest_order"]

        fields.append({
            "name": "Game Details",
            "value": f"{previous_message}"
                     f"**Event:**  {market_data.get('additional_data').get('game_title')}\n"
                     f"**Date:** {start_time}\n",
        })

        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\nTotal Over: ${over_data.get('total_liquidity', 0)} "
                     f"\nCost Avg Odds: {DiscordBot.format_odds(over_data.get('cost_avg_odds', 0))}\n\n"
                     f"Total Under: ${under_data.get('total_liquidity', 0)}"
                     f"\nCost Avg Odds: {DiscordBot.format_odds(under_data.get('cost_avg_odds', 0))}\n\n"
                     f"Highest Order: ${highest.get('liquidity_left', 0)} [{highest.get('side').title()}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(highest.get('american_price', 0))}\n```",
            "inline": False
        })

        link_fields = [
            {
                "name": f"{order_data.get('side').title()} {market_data.get('additional_data').get('line')} Link",
                "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
                "inline": False
            }
            for side, data in market_data.get("liquidity", {}).items()
            if (order_data := data.get("highest_order"))
        ]

        fields.extend(link_fields)

        return {
            "title": main_title,
            "color": 0x5D3A9B,
            "author": {
                "name": f"Novig Bot",
            },
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
