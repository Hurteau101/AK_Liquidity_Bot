import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discordwebhook import Discord
from team_mapper import nfl_team_map, nba_team_map


class DiscordBot:
    def __init__(self, league, market_type):
        load_dotenv()
        self.market_type = market_type
        self.league = league
        self.webhook = self._webhook_mapper(self.league, self.market_type)
        self.discord = Discord(url=self.webhook)

    def _webhook_mapper(self, league, market_type):
        MAPPER = {
            "props": {
                "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL_PROPS"),
                "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA_PROPS"),
            },
            "mainlines": {
                "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL_MAINLINES"),
                "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA_MAINLINES"),
                "ncaab": os.getenv("DISCORD_WEBHOOK_URL_NCAAB_MAINLINES"),
            }
        }

        if market_type.lower() not in MAPPER:
            raise ValueError(
                f"Market type '{market_type}' is not supported. "
                f"Supported market types: {list(MAPPER.keys())}"
            )

        league_keys = {key.lower() for key in MAPPER[market_type.lower()].keys()}
        if league.lower() not in league_keys:
            raise ValueError(
                f"League '{league}' is not supported for market type '{market_type}'. "
                f"Supported leagues: {list(league_keys)}"
            )

        return MAPPER.get(market_type).get(league.lower(), os.getenv("DISCORD_WEBHOOK_URL"))

    @staticmethod
    def format_odds(value: int | float) -> str:
        if value > 0:
            return f"+{value}"
        return str(value)

    def player_message(self, data, stat_type, line):
        player_name = data.get("additional_data").get("player_name")
        return f"{player_name} ({str(line)})"

    def game_message(self, data, stat_type, line):
        league_mapper = {
            "NFL": nfl_team_map,
            "NBA": nba_team_map,
        }
        mapper = league_mapper.get(self.league, {})

        bet_info = data.get("additional_data", {}).get("bet_info")
        if stat_type == "Spread":
            team_split = bet_info.split(" ")
            bet_info = f"{stat_type} {' '.join(team_split[1:])}"
        elif stat_type == "Moneyline":
            bet_info = stat_type
        elif stat_type == "Total":
            bet_info = str(line)
        elif stat_type == "Team Total":
            team_split = bet_info.split(" ")
            team_name = team_split[2:]
            team_name = " ".join(team_name)
            renamed_team = mapper.get(team_name.upper(), team_name)
            bet_info = f"{renamed_team} ({str(line)})"

        return bet_info


    def discord_message(self, data, market_changed=False):
        stat_type = data.get("additional_data").get("stat_type")
        line = data.get("additional_data").get("line")

        game_start_utc_str = data.get("additional_data").get("game_start_time")
        if game_start_utc_str:
            game_start_utc = datetime.fromisoformat(game_start_utc_str)
            eastern = ZoneInfo("America/New_York")
            game_start_eastern = game_start_utc.astimezone(eastern)
            game_start_time = game_start_eastern.strftime("%Y-%m-%d")
        else:
            game_start_time = "N/A"

        if data.get("additional_data", {}).get("type") == "player":
            main_title = self.player_message(data, stat_type, line)
        else:
            main_title = self.game_message(data, stat_type, line)


        notification = self.create_notification(main_title, game_start_time, data, market_changed, stat_type)

        self.discord.post(embeds=[notification])


    def create_notification(self, main_title, start_time, market_data, market_change, stat_type):
        fields = []

        previous_message = "*(Play was sent previously but market moved +/- 1000)*\n" if market_change else ""

        liquidity = market_data.get("liquidity", {})
        sides = list(liquidity.keys())

        # Moneyline / Spread
        if stat_type in ("Moneyline", "Spread"):
            side_1_name, side_2_name = sides[0], sides[1]
            side_1_data = liquidity.get(side_1_name, {}).get("highest_order", {})
            side_2_data = liquidity.get(side_2_name, {}).get("highest_order", {})
        # Totals (always over/under)
        else:
            side_1_name, side_2_name = "over", "under"
            side_1_data = liquidity.get("over", {}).get("highest_order", {})
            side_2_data = liquidity.get("under", {}).get("highest_order", {})

        # Find the overall highest order
        highest = max(
            liquidity.values(),
            key=lambda x: x["highest_order"]["total_liquidity"]
        )["highest_order"]

        fields.append({
            "name": "",
            "value": f"**Stat Type:** {stat_type}",
            "inline": False
        })

        fields.append({
            "name": "Game Details",
            "value": f"{previous_message}"
                     f"**Event:**  {market_data.get('additional_data', {}).get('game_title')}\n"
                     f"**Date:** {start_time}\n",
        })

       # Liquidity summary depends on stat_type
        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{side_1_name.upper() if stat_type in ['Moneyline', 'Spread'] else side_1_name.title()}: ${side_1_data.get('total_liquidity', 0)} "
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_1_data.get('cost_avg_odds', 0))}\n\n"
                     f"{side_2_name.upper() if stat_type in ['Moneyline', 'Spread'] else side_2_name.title()}: ${side_2_data.get('total_liquidity', 0)}"
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_2_data.get('cost_avg_odds', 0))}\n\n"
                     f"Highest Order: ${highest.get('liquidity_left', 0)} [{highest.get('side').title()}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(highest.get('american_price', 0))}\n```",
            "inline": False
        })

        # Links for each side
        link_fields = [
            {
                "name": (
                    f"{order_data.get('side').upper()} Link"
                    if stat_type in ("Moneyline", "Spread")
                    else f"{order_data.get('side').title()} {market_data.get('additional_data', {}).get('line')} Link"
                ),
                "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
                # "value": f"**↠** [Desktop]({order_data.get('desktop_link')})",
                "inline": False
            }
            for side, data in liquidity.items()
            if (order_data := data.get("highest_order"))
        ]

        fields.extend(link_fields)

        return {
            "title": main_title,
            "color": 0x5D3A9B,
            "author": {"name": "Novig Bot"},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # def mainline_message(self, data):
    #     stat_type = data.get("additional_data").get("stat_type")
    #
    #
    #
    # def prop_message(self, data, market_changed):
    #     stat_type = data.get("additional_data").get("stat_type")
    #     player_name = data.get("additional_data").get("player_name")
    #     line = data.get("additional_data").get("line")
    #
    #     game_start_utc_str = data.get("additional_data").get("game_start_time")
    #     if game_start_utc_str:
    #         game_start_utc = datetime.fromisoformat(game_start_utc_str)
    #         eastern = ZoneInfo("America/New_York")
    #         game_start_eastern = game_start_utc.astimezone(eastern)
    #         game_start_time = game_start_eastern.strftime("%Y-%m-%d")
    #     else:
    #         game_start_time = "N/A"
    #
    #     main_title = f"{player_name} {line} {stat_type}"
    #
    #     notification = self.create_notification(main_title, game_start_time, data, market_changed)
    #     self.discord.post(embeds=[notification])
    #
    #
    # def discord_message(self, data, market_changed=False):
    #     if self.market_type == "mainlines":
    #         self.mainline_message(data)
    #     elif self.market_type == "props":
    #         self.prop_message(data, market_changed)
    #
    #
    # @staticmethod
    # def format_odds(value: int | float) -> str:
    #     if value > 0:
    #         return f"+{value}"
    #     return str(value)
    #
    # def create_notification(self, main_title, start_time, market_data, market_change):
    #     fields = []
    #
    #     previous_message = "*(Play was sent previously but market moved +/- 1000)*\n" if market_change else ""
    #
    #     over_data = market_data.get("liquidity", {}).get("over", {}).get("highest_order", {})
    #     under_data = market_data.get("liquidity", {}).get("under", {}).get("highest_order", {})
    #
    #     highest = max(
    #         market_data["liquidity"].values(),
    #         key=lambda x: x["highest_order"]["total_liquidity"]
    #     )["highest_order"]
    #
    #     fields.append({
    #         "name": "Game Details",
    #         "value": f"{previous_message}"
    #                  f"**Event:**  {market_data.get('additional_data').get('game_title')}\n"
    #                  f"**Date:** {start_time}\n",
    #     })
    #
    #     fields.append({
    #         "name": "Liquidity Quick Summary",
    #         "value": f"```\nTotal Over: ${over_data.get('total_liquidity', 0)} "
    #                  f"\nCost Avg Odds: {DiscordBot.format_odds(over_data.get('cost_avg_odds', 0))}\n\n"
    #                  f"Total Under: ${under_data.get('total_liquidity', 0)}"
    #                  f"\nCost Avg Odds: {DiscordBot.format_odds(under_data.get('cost_avg_odds', 0))}\n\n"
    #                  f"Highest Order: ${highest.get('liquidity_left', 0)} [{highest.get('side').title()}]\n"
    #                  f"Highest Order Odds: {DiscordBot.format_odds(highest.get('american_price', 0))}\n```",
    #         "inline": False
    #     })
    #
    #     link_fields = [
    #         {
    #             "name": f"{order_data.get('side').title()} {market_data.get('additional_data').get('line')} Link",
    #             "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
    #             "inline": False
    #         }
    #         for side, data in market_data.get("liquidity", {}).items()
    #         if (order_data := data.get("highest_order"))
    #     ]
    #
    #     fields.extend(link_fields)
    #
    #     return {
    #         "title": main_title,
    #         "color": 0x5D3A9B,
    #         "author": {
    #             "name": f"Novig Bot",
    #         },
    #         "fields": fields,
    #         "timestamp": datetime.now(timezone.utc).isoformat()
    #     }
