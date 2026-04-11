import os
from abc import abstractmethod
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from discordwebhook import Discord
from dotenv import load_dotenv
from openpyxl.styles.builtins import title

from liqudity_context import LiquidityContext

load_dotenv()

class BaseNotification:
    def create_notification(self, title: str, liquidity_context: LiquidityContext, include_line: bool = True,
                            upper_case_highest_order_key: bool = True, upper_case_side_names: bool = True,
                            include_strategy_player_name: bool = False) -> dict:
        """
        Create a structured notification message based on the provided liquidity context and order data.
        :param title: The title of the notification
        :param liquidity_context: The context containing liquidity and additional data for the notification
        :param include_line: Whether to include the line for the links
        :param upper_case_highest_order_key: Whether to uppercase the side names in the liquidity summary
        :param upper_case_side_names: Whether to uppercase the side names in the liquidity summary
        """
        formated_game_date = self.get_time_pacific(game_start=liquidity_context.additional_data.get("game_start_time", ""))

        previously_sent = f"*(Play was sent previously but market moved +/- {liquidity_context.ping_movement_amount})*\n\n" \
            if liquidity_context.already_sent and not liquidity_context.strategy else ""

        # previously_sent = (
        #     f"*(Play was sent previously but market moved +/- {liquidity_context.ping_movement_amount})*\n\n"
        #     if liquidity_context.already_sent and liquidity_context.strategy is None else ""
        # )

        side_1_data = liquidity_context.main_liquidity.get(liquidity_context.side_1_name, {}).get("highest_order", {})
        side_2_data = liquidity_context.main_liquidity.get(liquidity_context.side_2_name, {}).get("highest_order", {})


        include_snapshot = liquidity_context.strategy.include_snapshot if liquidity_context.strategy else False
        snapshot_snippet = f"{liquidity_context.strategy.snapshot_time.strftime('%H:%M')} PST" if include_snapshot else ""

        side_1_name = liquidity_context.side_1_name.upper() if upper_case_side_names else liquidity_context.side_1_name.title()

        side_2_name = liquidity_context.side_2_name.upper() if upper_case_side_names else liquidity_context.side_2_name.title()

        highest_order_key = liquidity_context.highest_order_key.upper() if upper_case_highest_order_key else liquidity_context.highest_order_key.title()

        line = liquidity_context.additional_data.get('line')

        liquidity_summary = (


            f"```\n{side_2_name}{f' {line}' if include_line else ''}: ${side_2_data.get('total_liquidity', 0)}"
            f"\nCost Avg Odds: {SpreadNotification.format_odds(side_2_data.get('cost_avg_odds', 0))}\n\n"
            
            f"{side_1_name}{f' {line}' if include_line else ''}: ${side_1_data.get('total_liquidity', 0)}"
            f"\nCost Avg Odds: {SpreadNotification.format_odds(side_1_data.get('cost_avg_odds', 0))}\n\n"
            
            f"Highest Order: ${liquidity_context.highest_order.get('liquidity_left', 0)} [{highest_order_key}]\n"
            f"Highest Order Odds: {SpreadNotification.format_odds(liquidity_context.highest_order.get('american_price', 0))}\n\n"
            f"Liquidity Difference: ${liquidity_context.liquidity_difference}\n\n"
            f"{f'Snapshot Time: {snapshot_snippet}\n' if include_snapshot else ''}```"
        )

        fields = [
            {
                "name": "",
                "value": f"**Stat Type:** {liquidity_context.additional_data.get('stat_type', '')}",
                "inline": False
            },
            {
                "name": "",
                "value": f"**Player:** {liquidity_context.strategy.player_name}" if liquidity_context.strategy and liquidity_context.strategy.player_name else '',
                "inline": False
            },
            {
                "name": "Game Details",
                "value": f"**Event:**  {liquidity_context.additional_data.get('game_title', '')}\n"
                         f"**Date:** {formated_game_date} (PST)\n",
            },

            {
                "name": "Liquidity Quick Summary",
                "value": liquidity_summary
            }
        ]

        if previously_sent:
            fields.insert(1, {
                "name": "",
                "value": previously_sent,
                "inline": False
            })


        fields.extend([
            {
                "name": f"{order_data.get('side').title()} {liquidity_context.additional_data.get('line')} Link" if include_line else (
                    f"{order_data.get('side').upper()} Link"
                ),
                "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
                "inline": False
            }
            for side, data in liquidity_context.main_liquidity.items()
            if (order_data := data.get("highest_order"))
        ])

        return {
            "title": title,
            "color": 0x5D3A9B if not liquidity_context.strategy else liquidity_context.strategy.discord_color,
            "author": {"name": "Novig Bot"} if not liquidity_context.strategy else {"name": "Novig Strategy Bot"},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @abstractmethod
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        raise NotImplementedError("Subclasses must implement the format_notification method.")

    @staticmethod
    def get_time_pacific(game_start: str):
        """Convert to Pacific Time"""
        if game_start:
            game_start_utc = datetime.fromisoformat(game_start)
            pacific = ZoneInfo("America/Los_Angeles")
            game_start_pacific = game_start_utc.astimezone(pacific)
            game_start_time = game_start_pacific.strftime("%Y-%m-%d %I:%M %p")
        else:
            game_start_time = "N/A"

        return game_start_time

    @staticmethod
    def format_odds(value: int | float) -> str:
        if value > 0:
            return f"+{value}"

        if value == -100:
            return f"+100"

        return str(value)


class SpreadNotification(BaseNotification):
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        # title = liquidity_context.highest_order_key if liquidity_context.strategy is None else liquidity_context.strategy.strategy_name
        line = liquidity_context.additional_data.get("line", 0) if liquidity_context.strategy is None else liquidity_context.strategy.strategy_name
        if liquidity_context.strategy is None:
             title = f"+{str(line)}" if float(line) > 0 else str(line)
        else:
            title = liquidity_context.strategy.strategy_name


        return self.create_notification(
            title=title,
            liquidity_context=liquidity_context,
            include_line=False,
            upper_case_highest_order_key=True,
            upper_case_side_names=True
        )

class MoneylineNotification(SpreadNotification):
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        # raw_title = liquidity_context.highest_order_key if liquidity_context.strategy is None else liquidity_context.strategy.strategy_name
        # title = raw_title.upper() if len(raw_title) <= 3 else raw_title.title()

        return self.create_notification(
            title="Moneyline" if liquidity_context.strategy is None else liquidity_context.strategy.strategy_name,
            liquidity_context=liquidity_context,
            include_line=False,
            upper_case_highest_order_key=True,
            upper_case_side_names=True
        )

class FirstHalfSpreadNotification(SpreadNotification):
    pass

class TeamTotalNotification(BaseNotification):
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        team_name = " ".join(liquidity_context.additional_data.get('bet_info', "").split(" ")[2:])
        title = f"{team_name} ({liquidity_context.additional_data.get('line')})" if liquidity_context.strategy is None else (
            liquidity_context.strategy.strategy_name
        )

        return self.create_notification(
            title=title,
            liquidity_context=liquidity_context,
            include_line=False,
            upper_case_highest_order_key=False,
            upper_case_side_names=False
        )

class OverUnderNotification(BaseNotification):
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        title = str(liquidity_context.additional_data.get("line", "")) if liquidity_context.strategy is None else (
            liquidity_context.strategy.strategy_name
        )

        return self.create_notification(
            title=title,
            liquidity_context=liquidity_context,
            include_line=False,
            upper_case_highest_order_key=False,
            upper_case_side_names=False
        )


class PlayerNotification(BaseNotification):
    def format_notification(self, liquidity_context: LiquidityContext) -> dict:
        title = f"{liquidity_context.additional_data.get('player_name', '')} ({str(liquidity_context.additional_data.get('line', ''))})" if liquidity_context.strategy is None else (
            liquidity_context.strategy.strategy_name
        )

        return self.create_notification(
            title=title,
            liquidity_context=liquidity_context,
            include_line=False,
            upper_case_highest_order_key=False,
            upper_case_side_names=False
        )


class DiscordBot:
    def _regular_bot_mapper(self, league: str, market_type: str) -> str:
        """Returns the appropriate Discord webhook URL based on the provided league and market type."""
        if not league or not market_type:
            raise ValueError("Both 'league' and 'market_type' must be provided.")

        mapper = {
            "props": {
                "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL_PROPS"),
                "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA_PROPS"),
                "mlb": os.getenv("DISCORD_WEBHOOK_URL_MLB_PROPS"),
            },
            "mainlines": {
                "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL_MAINLINES"),
                "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA_MAINLINES"),
                "ncaab": os.getenv("DISCORD_WEBHOOK_URL_NCAAB_MAINLINES"),
                "mlb": os.getenv("DISCORD_WEBHOOK_URL_MLB_MAINLINES"),
            }
        }

        if market_type.lower() not in mapper:
            raise ValueError(
                f"Market type '{market_type}' is not supported. "
                f"Supported market types: {list(mapper.keys())}"
            )

        return mapper[market_type.lower()].get(league.lower(), None)


    def notification_controller(self, notification_type: str, liquidity_context: LiquidityContext):
        mapper = {
            "spread": SpreadNotification,
            "moneyline": MoneylineNotification,
            "player": PlayerNotification,
            "team total": TeamTotalNotification,
            "1st half spread": FirstHalfSpreadNotification,
        }

        notification_class = mapper.get(notification_type.lower(), OverUnderNotification)()
        return notification_class.format_notification(liquidity_context=liquidity_context)

    def notify(self, liquidity_context: LiquidityContext, webhook_url: str, role_id: str = None):
        notification_type = "player" if liquidity_context.additional_data.get("type") == "player" else (
            liquidity_context.additional_data.get("stat_type", "").lower())

        notification_message = self.notification_controller(notification_type=notification_type, liquidity_context=liquidity_context)
        discord = Discord(url=webhook_url)

        response = discord.post(
            content=f"<@&{role_id}>" if role_id else "",
            embeds=[notification_message]
        )

        if response.status_code != 204:
            print(f"Failed to send Discord message: {response.status_code} - {response.text}")

    def discord_message(self, liquidity_context: LiquidityContext):
        webook_url = self._regular_bot_mapper(league=liquidity_context.league, market_type=liquidity_context.market_type)

        if not webook_url:
            raise ValueError(f"No webhook found for league '{liquidity_context.league}' and market type '{liquidity_context.market_type}'."
                             f"Ensure you have it added to the mapper.")

        self.notify(liquidity_context=liquidity_context, webhook_url=webook_url)

class StrategyBot(DiscordBot):
    def _strategy_bot_mapper(self, league: str) -> str:
        """Returns the appropriate Discord webhook URL based on the provided league and market type."""
        if not league:
            raise ValueError("'league' must be provided.")

        mapper = {
            "nba": os.getenv("STRATEGY_BOT_WEBHOOK_URL_NBA"),
            "ncaab": os.getenv("STRATEGY_BOT_WEBHOOK_URL_NCAAB"),
            "mlb": os.getenv("STRATEGY_BOT_WEBHOOK_URL_MLB"),
        }

        return mapper[league.lower()]

    def discord_message(self, liquidity_context: LiquidityContext):
        webook_url = self._strategy_bot_mapper(league=liquidity_context.league)

        if not webook_url:
            raise ValueError(f"No webhook found for league '{liquidity_context.league}."
                             f"Ensure you have it added to the mapper.")


        role_id = os.getenv("ALERT_ROLE_ID") if liquidity_context.strategy.include_tag else None

        if liquidity_context.strategy.include_tag and role_id is None:
            raise ValueError("ALERT_ROLE_ID environment variable must be set if strategy includes tag.")


        self.notify(liquidity_context=liquidity_context, webhook_url=webook_url, role_id=role_id)

        # notification_type = "player" if liquidity_context.additional_data.get("type") == "player" else (
        #     liquidity_context.additional_data.get("stat_type", "").lower())
        #
        # notification_message = self.notification_controller(notification_type=notification_type, liquidity_context=liquidity_context)
        # discord = Discord(url=webook_url)
        # response = discord.post(embeds=[notification_message])
        # if response.status_code != 204:
        #     print(f"Failed to send Discord message: {response.status_code} - {response.text}")