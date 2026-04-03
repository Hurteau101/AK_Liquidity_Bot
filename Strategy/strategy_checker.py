from datetime import datetime, timezone, timedelta
import json
import redis
from Strategy.NBA.nba_strategies import NBASpreadSniper, NBASpreadExecutive, NBASpreadVolumeFavorites, NBASpreadVolume, \
    NBASpreadValueHunter, NBASpreadWhale, NBASpreadGodTier, NBATotalGoldUnder, NBATotalPlatinumUnder, NBATotalEliteOver, \
    NBATotalSilverUnder, NBATotalTrueSilverUnder

from liqudity_context import LiquidityContext, LiquidityStrategy
from discord_sender import StrategyBot
from Database.database import Database


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
    redis_unique_keys_instance = redis.Redis(host="localhost", port=6379, db=10, decode_responses=True)
    redis_strategy_sent_instance = redis.Redis(host="localhost", port=6379, db=9, decode_responses=True)

    for key in redis_unique_keys_instance.scan_iter("*"):
        raw_liquidity_data = redis_unique_keys_instance.get(key)

        if not raw_liquidity_data or redis_strategy_sent_instance.exists(key):
            continue

        liquidity_data = json.loads(raw_liquidity_data)

        start_date = liquidity_data.get("start_date", "")

        start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        modified_date = start_date_dt - timedelta(minutes=9)
        now_utc = datetime.now(timezone.utc)


        # We only want to check if we are within the 9 minute window before the game starts. If we are outside of that, we skip.
        if now_utc >= modified_date:
            matches = db.get_games(
                game_title=liquidity_data.get("game_title"),
                game_start_time=start_date_dt,
                league=liquidity_data.get("league"),
                stat_type=liquidity_data.get("stat_type")
            )

            if not matches:
                continue

            context_list = [
                LiquidityContext(
                    **{
                        **match.get("liquidity_context", {}),
                        "strategy": LiquidityStrategy(
                            snapshot_time=match.get("snapshot_time"),
                            include_tag=True,
                        )
                    }
                )
                for match in matches
            ]

            strategy_bot = StrategyBot()

            league = liquidity_data.get("league", "").upper()
            mapped_strategy = STRATEGIES.get(league, [])
            for strategy  in mapped_strategy:
                print("Checking strategy: ", strategy.__class__.__name__)
                if strategy.part_of_strategy(
                    stat_type=liquidity_data.get("stat_type", "").lower(), league=liquidity_data.get("league", "").lower()
                ) and strategy.run_match_analysis(liquidity_context=context_list, strategy_bot_instance=strategy_bot):
                    modified_start = start_date_dt + timedelta(minutes=60)

                    redis_strategy_sent_instance.set(
                        name=key,
                        value="",
                        exat=int(modified_start.timestamp())
                    )
                    break

