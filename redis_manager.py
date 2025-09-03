from datetime import datetime, timezone
import redis

from discord_sender import DiscordBot


class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
        self.discord_bot = DiscordBot()


    def check_player(self, player_key):
        return self.redis_client.exists(player_key) > 0

    def get_liquidity_difference(self, player_key):
        """Retrieve current liquidity difference for player if exists, else None."""
        return self.redis_client.hget(player_key, "liquidity_difference")

    def store_player(self, pipeline, player_key, liquidity_difference, start_time_dt):
        pipeline.hset(player_key, mapping={"liquidity_difference": liquidity_difference})
        pipeline.pexpireat(player_key, int(start_time_dt.timestamp() * 1000))
        pipeline.execute()


    def manger(self, player_data, league):
        if not player_data or not league:
            return

        pipeline = self.redis_client.pipeline()

        for player in player_data:
            player_key = player.get("key_name")
            redis_current_diff = self.get_liquidity_difference(player_key)

            start_date = player.get("additional_data", {}).get("game_start_time")
            start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            player_liquidity_difference = float(player.get("liqudity_difference", 0))

            if redis_current_diff is None:
                # New player
                self.store_player(pipeline, player_key, player_liquidity_difference, start_date_dt)
                self.discord_bot.discord_message(player, market_changed=False)

            elif abs(float(redis_current_diff) - player_liquidity_difference) >= 1000:
                # Existing player but difference changed a lot
                self.store_player(pipeline, player_key, player_liquidity_difference, start_date_dt)
                self.discord_bot.discord_message(player, market_changed=True)