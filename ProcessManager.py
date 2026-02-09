import json
from datetime import datetime, timezone, timedelta
from enum import Enum

import redis
from database import Database
from discord_sender import DiscordBot
import json

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


    def get_liquidity_difference(self, player_key):
        """Retrieve current liquidity difference for player if exists, else None."""
        return self.redis_client.hget(player_key, "liquidity_difference")


    def store_player(self, pipeline, player_key, start_time_dt, mapping_data: dict):
        pipeline.hset(player_key, mapping=mapping_data)
        pipeline.pexpireat(player_key, int(start_time_dt.timestamp() * 1000))
        pipeline.execute()


    def strategy_runner(self, player_data: dict, player_key: str, start_time_dt: datetime):
        redis_instance = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)
        pipeline = redis_instance.pipeline()

        player_liq_data = self.strategy_storer(player_data=player_data, player_key=player_key, start_time_dt=start_time_dt, redis_instance=redis_instance, pipeline=pipeline)
        self.strategy_checker(
            player_data=player_liq_data,
            start_date=start_time_dt,
        )


    def strategy_checker(self, player_data: dict, start_date: datetime):
        modified_date = start_date - timedelta(minutes=9)
        now_utc = datetime.now(timezone.utc)
        if now_utc >= modified_date:
            highest_order = max(
                player_data.get("liquidity").values(),
                key=lambda x: x["highest_order"]["total_liquidity"]
            )["highest_order"]

            liquidity_difference = player_data.get("liqudity_difference")

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

    def strategy_storer(self, player_data: dict, player_key: str, start_time_dt: datetime, redis_instance: redis.Redis, pipeline):
        found_player = redis_instance.exists(player_key)

        mapping_data = {
            "player_data": json.dumps(player_data),
        }

        if found_player:
            previous_data = redis_instance.hget(player_key, "player_data")
            previous_player_dict = json.loads(previous_data)

            previous_highest_order = max(
                previous_player_dict.get("liquidity").values(),
                key=lambda x: x["highest_order"]["total_liquidity"]
            )["highest_order"]

            current_highest_order = max(
                player_data.get("liquidity").values(),
                key=lambda x: x["highest_order"]["total_liquidity"]
            )["highest_order"]

            if current_highest_order.get("liquidity_left") <= previous_highest_order.get("liquidity_left"):
                return previous_player_dict # Return previous player since its the highest still.

        self.store_player(pipeline=pipeline, player_key=player_key, start_time_dt=start_time_dt,
                          mapping_data=mapping_data)

        return player_data # Return new data as its the highest.


    def manger(self, player_data, league):
        if not player_data or not league:
            return

        pipeline = self.redis_client.pipeline()
        db = Database()

        for player in player_data:
            player_key = player.get("key_name")
            redis_current_diff = self.get_liquidity_difference(player_key)

            start_date = player.get("additional_data", {}).get("game_start_time")
            start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            # Add 30 minutes buffer to expiration time due to Novig keeping data for a bit longer after start time.
            start_date_dt_plus_buffer = start_date_dt + timedelta(minutes=30)

            player_liquidity_difference = float(player.get("liqudity_difference", 0))

            mapping_data = {"liquidity_difference": player_liquidity_difference}

            if redis_current_diff is None:
                # New player
                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data,start_time_dt=start_date_dt_plus_buffer)
                self.discord_bot.discord_message(player, market_changed=False)
                db.insert_data(player, league, self.market_type)


            elif abs(float(redis_current_diff) - player_liquidity_difference) >= self.difference_amount:
                # Existing player but difference changed a lot
                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data, start_time_dt=start_date_dt)
                self.discord_bot.discord_message(player, market_changed=True)
                db.insert_data(player, league, self.market_type)

            if league == "NBA" and self.market_type == "mainlines" and player.get("additional_data", {}).get(
                    "stat_type") == "Spread":
                self.strategy_runner(
                    player_data=player,
                    player_key=player_key,
                    start_time_dt=start_date_dt,
                )
