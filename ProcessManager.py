import json
from datetime import datetime, timezone, timedelta
from enum import Enum

import redis
from redis import Redis

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


    # def strategy_checker(self, strategy_redis: redis.Redis, already_sent_redis: redis.Redis, db:Database):
    #     all_data = strategy_redis.keys("*")
    #
    #     stored_values = {
    #         key: json.loads(player_data)
    #         for key in all_data
    #         if key
    #         for player_data in strategy_redis.hgetall(key).values()
    #     }
    #
    #
    #     for key, value in stored_values.items():
    #         start_date = value.get("additional_data", {}).get("game_start_time")
    #         start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    #
    #         modified_date = start_date_dt - timedelta(minutes=9)
    #         now_utc = datetime.now(timezone.utc)
    #
    #         already_sent = already_sent_redis.exists(key)
    #
    #         if not already_sent and now_utc >= modified_date:
    #             matches = db.get_games(
    #                 game_title=key,
    #                 game_start_time=start_date_dt,
    #                 league=value.get("league"),
    #                 stat_type=value.get("additional_data", {}).get("stat_type")
    #             )
    #
    #             if not matches:
    #                 return
    #
    #             highest_order = max(
    #                 matches,
    #                 key=lambda x: x["liquidity_highest_order"]
    #             )
    #
    #             liquidity_difference = float(highest_order.get("liquidity_difference", 0))
    #             odds = float(highest_order.get("odds_highest_order", 0))
    #             liquidity_highest_order = float(highest_order.get("liquidity_highest_order", 0))
    #             is_favorite = True if "-" in highest_order.get("stat_type") else False
    #
    #
    #             print("Potential Strategy Match")
    #
    #             strategy_bot = StrategyDiscordBot()
    #             strategy = None
    #
    #             if all([
    #                 is_favorite,
    #                 SpreadSniper.LOW_ODDS.value <= odds <= SpreadSniper.HIGH_ODDS.value,
    #                 SpreadSniper.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadSniper.HIGH_HIGHEST_ORDER.value,
    #                 SpreadSniper.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadSniper.HIGH_LIQ_DIFFERENCE.value,
    #             ]):
    #                 strategy = "Sniper"
    #
    #             elif all([
    #                 SpreadExecutive.LOW_ODDS.value <= odds <= SpreadExecutive.HIGH_ODDS.value,
    #                 SpreadExecutive.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadExecutive.HIGH_HIGHEST_ORDER.value,
    #                 SpreadExecutive.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadExecutive.HIGH_LIQ_DIFFERENCE.value,
    #             ]):
    #                 strategy = "Executive"
    #
    #             elif all([
    #                 SpreadVolume.LOW_ODDS.value <= odds <= SpreadVolume.HIGH_ODDS.value,
    #                 SpreadVolume.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadVolume.HIGH_HIGHEST_ORDER.value
    #             ]):
    #                 strategy = "Volume"
    #
    #             if strategy:
    #                 print(f"Strategy Match: {strategy}")
    #                 already_sent_redis.set(name=key, ex=int(start_date_dt.timestamp() * 1000), value="")
    #
    #                 strategy_bot.discord_message(
    #                     highest_order=highest_order,
    #                     market_data=value,
    #                     strategy_type=strategy,
    #                     stat_type="Spread",
    #                     liquidity_difference=liquidity_difference
    #                 )
    #             else:
    #                 print("No Strategy Match")

    # def strategy_storer(self, player_data: dict, start_time_dt: datetime, redis_instance: redis.Redis, pipeline):
    #     game_key = player_data.get("additional_data", {}).get("game_title")
    #     found_player = redis_instance.exists(game_key)
    #
    #     if found_player:
    #         return
    #
    #     redis_instance.set(name=game_key, ex=int(start_time_dt.timestamp() * 1000), value="")


        # mapping_data = {
        #     "player_data": json.dumps(player_data),
        # }
        #
        # if found_player:
        #     previous_data = redis_instance.hget(game_key, "player_data")
        #     previous_player_dict = json.loads(previous_data)
        #     previous_highest_order = max(
        #         previous_player_dict.get("liquidity").values(),
        #         key=lambda x: x["highest_order"]["liquidity_left"]
        #     )["highest_order"]
        #
        #     current_highest_order = max(
        #         player_data.get("liquidity").values(),
        #         key=lambda x: x["highest_order"]["liquidity_left"]
        #     )["highest_order"]
        #
        #     if current_highest_order.get("liquidity_left") <= previous_highest_order.get("liquidity_left"):
        #         return
        #
        # self.store_player(pipeline=pipeline, player_key=game_key, start_time_dt=start_time_dt,
        #                   mapping_data=mapping_data)

    def check_strategy(self, league, player, start_date_dt, redis: Redis, redis_pipeline):
        if league == "NBA" and self.market_type == "mainlines" and player.get("additional_data", {}).get(
                "stat_type") == "Spread":

            game_key = player.get("additional_data", {}).get("game_title")
            found_player = redis.exists(game_key)

            if found_player:
                return

            mapping_data = {
                "player_data": json.dumps({
                    **player,
                    "league": league,
                }),
            }

            self.store_player(pipeline=redis_pipeline, player_key=game_key, start_time_dt=start_date_dt,
                              mapping_data=mapping_data)


    def manger(self, player_data, league):
        if not player_data or not league:
            return

        redis_strategy_instance = redis.Redis(host="localhost", port=6379, db=8, decode_responses=True)
        strategy_pipeline = redis_strategy_instance.pipeline()
        # redis_strategy_sent_instance = redis.Redis(host="localhost", port=6379, db=9, decode_responses=True)

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
                self.check_strategy(league=league, player=player, start_date_dt=start_date_dt, redis=redis_strategy_instance, redis_pipeline=strategy_pipeline)
                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data,start_time_dt=start_date_dt_plus_buffer)
                self.discord_bot.discord_message(player, market_changed=False)
                db.insert_data(player, league, self.market_type)


            elif abs(float(redis_current_diff) - player_liquidity_difference) >= self.difference_amount:
                # Existing player but difference changed a lot
                self.check_strategy(league=league, player=player, start_date_dt=start_date_dt, redis=redis_strategy_instance, redis_pipeline=strategy_pipeline)
                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data, start_time_dt=start_date_dt)
                self.discord_bot.discord_message(player, market_changed=True)
                db.insert_data(player, league, self.market_type)


        # if league == "NBA" and self.market_type == "mainlines":
        #     self.strategy_checker(already_sent_redis=redis_strategy_sent_instance, strategy_redis=redis_strategy_instance, db=db)

