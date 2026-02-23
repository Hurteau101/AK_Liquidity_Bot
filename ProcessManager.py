import os
from datetime import datetime, timezone, timedelta
import re
import redis
from redis import Redis
from database import Database
from discord_sender import DiscordBot
import json



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


    def store_game(self, game_title: str, start_date_dt, redis: Redis, redis_pipeline, league: str, stat_type: str):
        if not all([game_title, league, stat_type]):
            return

        game_key = re.sub(
            r"_+",
            "_",
            f"{game_title}_{stat_type}_{league}"
            .replace("@", "_")
            .replace(" ", "_")
            .lower()
        )

        found_player = redis.exists(game_key)

        if found_player:
            return

        mapping_data = {
            "game_data": json.dumps({
                "game_title": game_title,
                "start_date": start_date_dt.isoformat(),
                "league": league,
                "stat_type": stat_type
            }),
        }

        self.store_player(pipeline=redis_pipeline, player_key=game_key, start_time_dt=start_date_dt,
                          mapping_data=mapping_data)


    def manger(self, player_data, league):
        if not player_data or not league:
            return

        is_production = os.getenv("PRODUCTION") == "True"

        redis_strategy_instance = redis.Redis(host="localhost", port=6379, db=8, decode_responses=True)
        strategy_pipeline = redis_strategy_instance.pipeline()

        pipeline = self.redis_client.pipeline()
        db = Database()

        for player in player_data:

            # Ensure crazy high odds aren't stored or pinged.
            if all(
                    side_data["highest_order"]["cost_avg_odds"] >= 250
                    for side_data in player["liquidity"].values()
            ):
                continue

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
                self.store_game(game_title=player.get("additional_data", {}).get("game_title"),
                                start_date_dt=start_date_dt, redis=redis_strategy_instance, redis_pipeline=strategy_pipeline,
                                league=league, stat_type=player.get("additional_data", {}).get("stat_type"))

                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data,start_time_dt=start_date_dt_plus_buffer)
                self.discord_bot.discord_message(player, market_changed=False)

                if is_production:
                    db.insert_data(player, league, self.market_type)


            elif abs(float(redis_current_diff) - player_liquidity_difference) >= self.difference_amount:
                # Existing player but difference changed a lot
                self.store_game(game_title=player.get("additional_data", {}).get("game_title"),
                                start_date_dt=start_date_dt, redis=redis_strategy_instance, redis_pipeline=strategy_pipeline,
                                league=league, stat_type=player.get("additional_data", {}).get("stat_type"))

                self.store_player(pipeline=pipeline, player_key=player_key, mapping_data=mapping_data, start_time_dt=start_date_dt)
                self.discord_bot.discord_message(player, market_changed=True)

                if is_production:
                    db.insert_data(player, league, self.market_type)