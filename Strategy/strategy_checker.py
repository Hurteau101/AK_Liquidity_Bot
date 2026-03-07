from datetime import datetime, timezone, timedelta
import json
import redis
from Strategy.NBA.nba_strategies import NBASpreadSniper, NBASpreadVolume, NBASpreadExecutive, NBASpreadWhale, \
    NBATotalGoldUnder, NBATotalPlatinumUnder, NBATotalEliteOver, NBATotalSilverUnder, NBATotalTrueSilverUnder, \
    NBASpreadValueHunter, NBASpreadVolumeFavorites, NBASpreadGodTier
from Strategy.NCAAB.ncaab_strategies import NCAABTotalSkyHigh, NCAABTotalUnder, NCAABTotalGoldMine, NCAABTotalLowLine, NCAABTotalOverHighJuice
from database import Database
from strategy_bot_sender import StrategyDiscordBot

# Order matters
STRATEGIES = {
    "NBA": [
        NBASpreadValueHunter(),
        NBASpreadGodTier(),
        NBASpreadWhale(),
        NBASpreadVolumeFavorites(),
        NBASpreadSniper(),
        NBASpreadExecutive(),
        NBASpreadVolume(),

        NBATotalGoldUnder(),
        NBATotalPlatinumUnder(),
        NBATotalEliteOver(),
        NBATotalTrueSilverUnder(),
        NBATotalSilverUnder()
    ]
}


def run_strategy_check():
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
        start_date = value.get("start_date", {})
        start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        modified_date = start_date_dt - timedelta(minutes=9)
        now_utc = datetime.now(timezone.utc)

        already_sent = redis_strategy_sent_instance.exists(key)

        if not already_sent and now_utc >= modified_date:
            matches = db.get_games(
                game_title=value.get("game_title"),
                game_start_time=start_date_dt,
                league=value.get("league"),
                stat_type=value.get("stat_type")
            )

            if not matches:
                continue

            strategy_bot = StrategyDiscordBot()

            league = value.get("league").upper()
            mapped_strategy = STRATEGIES.get(league, [])

            for strategy in mapped_strategy:
                print("Checking strategy: ", strategy.__class__.__name__)
                if strategy.part_of_strategy(
                        stat_type=value.get("stat_type").lower(), league=value.get("league").lower()
                ) and strategy.run_match_analysis(matches=matches, strategy_bot_instance=strategy_bot, start_date=start_date):
                    redis_strategy_sent_instance.set(name=key, ex=int(start_date_dt.timestamp() * 1000), value="")
                    print("- Match found")
                    break # Break since then a message was sent.
                print("- No match found")


# run_strategy_check()