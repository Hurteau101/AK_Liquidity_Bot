from datetime import datetime, timezone, timedelta
import json
from enum import Enum
import redis
from database import Database
from strategy_bot_sender import StrategyDiscordBot


class SpreadSniper(Enum):
    LOW_ODDS = -110
    HIGH_ODDS = 1100
    LOW_HIGHEST_ORDER = 5250
    HIGH_HIGHEST_ORDER = 74000
    LOW_LIQ_DIFFERENCE = 4100
    HIGH_LIQ_DIFFERENCE = 83500

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


def strategy_checker():
    db = Database()
    redis_strategy_instance = redis.Redis(host="localhost", port=6379, db=8, decode_responses=True)
    redis_strategy_sent_instance = redis.Redis(host="localhost", port=6379, db=9, decode_responses=True)

    all_data = redis_strategy_instance.keys("*")

    stored_values = {
        key: json.loads(player_data)
        for key in all_data
        if key
        for player_data in redis_strategy_instance.hgetall(key).values()
    }

    for key, value in stored_values.items():
        start_date = value.get("additional_data", {}).get("game_start_time")
        start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

        modified_date = start_date_dt - timedelta(minutes=9)
        now_utc = datetime.now(timezone.utc)


        already_sent = redis_strategy_sent_instance.exists(key)

        if not already_sent and now_utc >= modified_date:
            matches = db.get_games(
                game_title=key,
                game_start_time=start_date_dt,
                league=value.get("league"),
                stat_type=value.get("additional_data", {}).get("stat_type")
            )

            if not matches:
                return

            highest_order = max(
                matches,
                key=lambda x: x["liquidity_highest_order"]
            )


            liquidity_difference = float(highest_order.get("liquidity_difference", 0))
            odds = float(highest_order.get("odds_highest_order", 0))
            liquidity_highest_order = float(highest_order.get("liquidity_highest_order", 0))
            is_favorite = True if "-" in highest_order.get("stat_type") else False

            print("Potential Strategy Match")

            strategy_bot = StrategyDiscordBot()
            strategy = None

            if all([
                # is_favorite,
                SpreadSniper.LOW_ODDS.value <= odds <= SpreadSniper.HIGH_ODDS.value,
                SpreadSniper.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadSniper.HIGH_HIGHEST_ORDER.value,
                SpreadSniper.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadSniper.HIGH_LIQ_DIFFERENCE.value,
            ]):
                strategy = "Sniper"

            elif all([
                SpreadExecutive.LOW_ODDS.value <= odds <= SpreadExecutive.HIGH_ODDS.value,
                SpreadExecutive.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadExecutive.HIGH_HIGHEST_ORDER.value,
                SpreadExecutive.LOW_LIQ_DIFFERENCE.value <= liquidity_difference <= SpreadExecutive.HIGH_LIQ_DIFFERENCE.value,
            ]):
                strategy = "Executive"

            elif all([
                SpreadVolume.LOW_ODDS.value <= odds <= SpreadVolume.HIGH_ODDS.value,
                SpreadVolume.LOW_HIGHEST_ORDER.value <= liquidity_highest_order <= SpreadVolume.HIGH_HIGHEST_ORDER.value
            ]):
                strategy = "Volume"

            if strategy:
                print(f"Strategy Match: {strategy}")
                redis_strategy_sent_instance.set(name=key, ex=int(start_date_dt.timestamp() * 1000), value="")

                strategy_bot.discord_message(
                    order_details=highest_order,
                    strategy_type=strategy,
                    game_time=start_date
                )
            else:
                print("No Strategy Match")


strategy_checker()