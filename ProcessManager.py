from datetime import datetime, timezone, timedelta
import redis
from enum import Enum
from database import Database
from discord_sender import DiscordBot
from strategy_bot_sender import StrategyDiscordBot


class SpreadSniper(Enum):
    LOW_ODDS = -110
    HIGH_ODDS = 110
    LOW_HIGHEST_ORDER = 5250
    HIGH_HIGHEST_ORDER = 7400
    LOW_LIQ_DIFFERENCE = 4100
    HIGH_LIQ_DIFFERENCE = 8350

class SpreadExecutive(Enum):
    LOW_ODDS = -110
    HIGH_ODDS = 110
    LOW_HIGHEST_ORDER = 5000
    HIGH_HIGHEST_ORDER = 7500
    LOW_LIQ_DIFFERENCE = 4000
    HIGH_LIQ_DIFFERENCE = 8500

class SpreadVolume(Enum):
    LOW_ODDS = -125
    HIGH_ODDS = 125
    LOW_HIGHEST_ORDER = 4800
    HIGH_HIGHEST_ORDER = 6000

class ProcessManager:
    def __init__(self, league, redis_database=1, difference_amount=1000, market_type="mainlines"):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=redis_database, decode_responses=True)
        self.difference_amount = difference_amount
        self.discord_bot = DiscordBot(league, market_type)
        self.market_type = market_type

    def check_player(self, player_key):
        return self.redis_client.exists(player_key) > 0


    def get_previous_data(self, player_key) -> dict:
        """Retrieve previous liquidity data for player if exists, else None."""
        return self.redis_client.hgetall(player_key)

    def store_player(self, pipeline, player_key, liquidity_difference, start_time_dt, highest_order: float):
        pipeline.hset(player_key, mapping={
            "liquidity_difference": liquidity_difference,
            "highest_order": highest_order
        })
        pipeline.pexpireat(player_key, int(start_time_dt.timestamp() * 1000))
        pipeline.execute()

    def strategy_checker(self, player_data: dict, start_date: datetime, highest_order: dict, player_key: str, liquidity_difference: float):
        """Used to check if it needs to send the strategy"""
        modified_date = start_date - timedelta(minutes=9)
        now_utc = datetime.now(timezone.utc)

        if modified_date >= now_utc:
            redis_instance = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)
            found_player = redis_instance.exists(player_key)
            if not found_player:
                redis_instance.set(name=player_key, ex=int(start_date.timestamp() * 1000), value="")

                strategy_bot = StrategyDiscordBot()
                strategy = None

                if all([
                    highest_order["cost_avg_odds"] > 0,
                    SpreadSniper.LOW_ODDS.value <= highest_order.get("cost_avg_odds",
                                                                     0) <= SpreadSniper.HIGH_ODDS.value,
                    SpreadSniper.LOW_HIGHEST_ORDER.value <= highest_order.get("liquidity_left",
                                                                              0) <= SpreadSniper.HIGH_HIGHEST_ORDER.value,
                    SpreadSniper.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadSniper.HIGH_LIQ_DIFFERENCE.value,
                ]):
                    strategy = "Sniper"

                elif all([
                    SpreadExecutive.LOW_ODDS.value <= highest_order.get("cost_avg_odds",
                                                                        0) <= SpreadExecutive.HIGH_ODDS.value,
                    SpreadExecutive.LOW_HIGHEST_ORDER.value <= highest_order.get("liquidity_left",
                                                                                 0) <= SpreadExecutive.HIGH_HIGHEST_ORDER.value,
                    SpreadExecutive.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadExecutive.HIGH_LIQ_DIFFERENCE.value,
                ]):
                    strategy = "Executive"

                elif all([
                    SpreadVolume.LOW_ODDS.value <= highest_order.get("cost_avg_odds",
                                                                     0) <= SpreadVolume.HIGH_ODDS.value,
                    SpreadVolume.LOW_HIGHEST_ORDER.value <= highest_order.get("liquidity_left",
                                                                              0) <= SpreadVolume.HIGH_HIGHEST_ORDER.value
                ]):
                    strategy = "Volume"

                if strategy:
                    strategy_bot.discord_message(
                        highest_order=highest_order,
                        market_data=player_data,
                        strategy_type=strategy,
                        stat_type="Spread",
                        liquidity_difference=liquidity_difference
                    )

    def manger(self, player_data, league):
        if not player_data or not league:
            return

        pipeline = self.redis_client.pipeline()
        db = Database()

        for player in player_data:
            highest_order = max(
                player.get("liquidity").values(),
                key=lambda x: x["highest_order"]["total_liquidity"]
            )["highest_order"]

            player_key = player.get("key_name")
            previous_data = self.get_previous_data(player_key)

            start_date = player.get("additional_data", {}).get("game_start_time")
            start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            # Add 30 minutes buffer to expiration time due to Novig keeping data for a bit longer after start time.
            start_date_dt_plus_buffer = start_date_dt + timedelta(minutes=30)

            player_liquidity_difference = float(player.get("liqudity_difference", 0))
            highest_order_liquidity = float(highest_order.get("liquidity_left", 0))

            if previous_data is None:
                # New player
                self.store_player(pipeline, player_key, player_liquidity_difference, start_date_dt_plus_buffer, highest_order_liquidity)
                self.discord_bot.discord_message(player, market_changed=False)
                db.insert_data(player, league, self.market_type)

            elif abs(float(previous_data.get("liquidity_difference", 0.00)) - player_liquidity_difference) >= self.difference_amount:
                # Existing player but difference changed a lot
                self.store_player(pipeline, player_key, player_liquidity_difference, start_date_dt, highest_order_liquidity)
                self.discord_bot.discord_message(player, market_changed=True)
                db.insert_data(player, league, self.market_type)

            if league == "NBA" and self.market_type == "mainlines" and player.get("additional_data", {}).get("stat_type") == "Spread":
                self.strategy_checker(player_data=player, start_date=start_date_dt, highest_order=highest_order,
                                      player_key=player_key, liquidity_difference=player_liquidity_difference)
