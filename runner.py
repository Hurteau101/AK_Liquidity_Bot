import asyncio
import re
from collections import defaultdict
from datetime import datetime, timedelta
import redis
from novig import Novig
import json
from Database.database import Database
from Strategy.NCAAB.ncaab_strategies import NCAABTotalSkyHigh, NCAABTotalUnder, NCAABTotalGoldMine, NCAABTotalLowLine, \
    NCAABTotalOverHighJuice
from discord_sender import DiscordBot, StrategyBot
from liqudity_context import LiquidityContext, LiquidityStrategy

STRATEGIES_PER_RUN = {
    "NCAAB": [
        NCAABTotalSkyHigh(),
        NCAABTotalUnder(),
        NCAABTotalGoldMine(),
        NCAABTotalLowLine(),
        NCAABTotalOverHighJuice(),
    ]
}
class Runner:
    def __init__(self, database_instance: Database, mapping_data: dict):
        self.database = database_instance
        self.mapping = mapping_data
        self.discord_bot = DiscordBot()
        self.strategy_bot = StrategyBot()
        # Store Strategies
        self.redis_strategy = redis.Redis(host="localhost", port=6379, db=9, decode_responses=True)
        # Store Previously Sent
        self.redis_sent = redis.Redis(host="localhost", port=6379, db=8, decode_responses=True)
        # Store Unique Keys
        self.redis_unique_keys = redis.Redis(host="localhost", port=6379, db=10, decode_responses=True)


    def set_key(self, start_date: datetime, liquidity_key: str, liquidity_data: dict):
        if start_date is None or not liquidity_key or liquidity_data is None:
            raise ValueError("start_date, liquidity_key, and liquidity_data must be provided")

        ttl_seconds = int(
            (start_date - datetime.now(tz=start_date.tzinfo)).total_seconds()
        )

        # ### REMOVE THIS AFTERWARDS
        # self.redis_sent.setex(name=liquidity_key, value=json.dumps({liquidity_key: liquidity_data}), time=120000)
        # ##########################


        self.redis_sent.setex(name=liquidity_key, value=json.dumps({liquidity_key: liquidity_data}), time=ttl_seconds)


    def check_strategy(self, liquidity_context: LiquidityContext):
        if not liquidity_context.run_strategy_per_run:
            return

        sent_already = self.redis_strategy.get(liquidity_context.liquidity_key)
        if sent_already:
            return

        # Initialize strategy in context for use in strategies and discord message - Initialziing here
        # so we can pass in `include_tag`
        liquidity_context.strategy = LiquidityStrategy(
            include_tag=True
        )

        league_strategy = STRATEGIES_PER_RUN.get(liquidity_context.league.upper(), [])

        for strategy in league_strategy:
            if (
                    strategy.part_of_strategy(league=liquidity_context.league.lower(),
                                              stat_type=liquidity_context.additional_data.get("stat_type", '').lower())
                    and
                    strategy.run_match_analysis(liquidity_context=liquidity_context, strategy_bot_instance=self.strategy_bot)):
                self.redis_strategy.set(name=liquidity_context.liquidity_key, ex=int(liquidity_context.start_date_buffer.timestamp() * 1000), value="")
                break

    def store_unique_key(self, game_title: str, start_date_dt: datetime, league: str, stat_type: str):
        """This is used to store a unique key containing the league, game title and stat type"""
        if not all([game_title, start_date_dt, league, stat_type]):
            return

        game_key = re.sub(
            r"_+",
            "_",
            f"{game_title}_{stat_type}_{league}"
            .replace("@", "_")
            .replace(" ", "_")
            .lower()
        )

        found_key = self.redis_unique_keys.exists(game_key)
        if found_key:
            return

        self.redis_unique_keys.setex(name=game_key, value=json.dumps({
            "game_title": game_title,
            "start_date": start_date_dt.isoformat(),
            "league": league,
            "stat_type": stat_type
        }), time=int(start_date_dt.timestamp() * 1000))


    def process_liquidity(self, liquidity_context: LiquidityContext):
        self.set_key(start_date=liquidity_context.start_date_buffer, liquidity_key=liquidity_context.liquidity_key,
                     liquidity_data={**liquidity_context.main_liquidity, **liquidity_context.additional_data,
                                     "liquidity_difference": liquidity_context.liquidity_difference,
                                     "league": liquidity_context.league})
        self.store_unique_key(
            game_title=liquidity_context.additional_data.get("game_title", ""),
            start_date_dt=liquidity_context.start_date_dt,
            league=liquidity_context.league,
            stat_type=liquidity_context.additional_data.get("stat_type", "")
        )
        self.discord_bot.discord_message(liquidity_context=liquidity_context)
        self.check_strategy(liquidity_context=liquidity_context)
        self.database.controller(liquidity_context=liquidity_context)


    def check_liquidity(self, liquidity_data: dict):
        for league, liquidity_list in liquidity_data.items():
            for liquidity in liquidity_list:
                print(liquidity)
                selection_key = (league, liquidity.get("additional_data", {}).get("stat_type"))
                found_mapping = self.mapping.get(selection_key)

                if not found_mapping:
                    print("No Mapping Found for Selection Key:", selection_key)
                    continue


                highest_order_key = max(
                    liquidity["liquidity"],
                    key=lambda k: liquidity["liquidity"][k]["highest_order"]["total_liquidity"]
                )

                highest_order = liquidity["liquidity"][highest_order_key]["highest_order"]

                highest_odds = max(
                    liquidity["liquidity"].values(),
                    key=lambda x: x["highest_order"]["cost_avg_odds"]
                )["highest_order"].get("cost_avg_odds", 0)


                highest_order_amount = highest_order.get("liquidity_left")
                liquidity_difference = liquidity.get("liquidity_difference")
                filtered_highest_odds_restriction = found_mapping.get("max_odds")

                if any([
                    highest_order_amount < (found_mapping.get("liquidity_difference_filter_amount") or 0),
                    liquidity_difference < (found_mapping.get("highest_order_filter_amount") or 0),
                    (filtered_highest_odds_restriction and highest_odds > filtered_highest_odds_restriction)
                ]):
                    continue


                liquidity_key = liquidity.get("key_name")
                redis_key = f"{league}_{liquidity_key}"

                start_date = liquidity.get("additional_data", {}).get("game_start_time")

                start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                # Add 30 minutes buffer to expiration time due to Novig keeping data for a bit longer after start time.
                start_date_dt_plus_buffer = start_date_dt + timedelta(minutes=30)

                sides = list(liquidity.get("liquidity").keys())
                side_1_name, side_2_name = sides[0], sides[1]


                context = LiquidityContext(
                    league=league,
                    market_type=found_mapping.get("market_selection"),
                    ping_movement_amount=found_mapping.get("ping_difference_amount", 0),
                    already_sent=False,
                    found_mapping=found_mapping,
                    highest_order=highest_order,
                    highest_order_key=highest_order_key if highest_order_key not in ['over', 'under'] else highest_order_key.title(),
                    liquidity_key=redis_key,
                    start_date_dt=start_date_dt,
                    start_date_buffer=start_date_dt_plus_buffer,
                    main_liquidity=liquidity.get("liquidity", {}),
                    additional_data=liquidity.get("additional_data", {}),
                    liquidity_difference=liquidity_difference,
                    run_strategy_per_run=found_mapping.get("run_strategy_per_run", False),
                    side_1_name=side_1_name,
                    side_2_name=side_2_name,
                )

                previous_liquidity_raw = self.redis_sent.get(redis_key)

                if previous_liquidity_raw is None:
                    print("New Liquidity Found")
                    self.process_liquidity(liquidity_context=context)
                    continue

                previous_liquidity = json.loads(previous_liquidity_raw)

                matched_liquidity = previous_liquidity.get(redis_key)

                if not matched_liquidity:
                    continue

                previous_liquidity_difference = float(matched_liquidity.get("liquidity_difference", 0))

                if abs(previous_liquidity_difference - liquidity_difference) >= found_mapping.get("ping_difference_amount", 0):
                    context.already_sent = True
                    self.process_liquidity(liquidity_context=context)

    async def extract_liquidity(self, filter_data: dict):
        """Extracts liquidity data based on the provided filter data"""
        novig = Novig(filters=filter_data, filter_amount_dict={"filter_type": "liquidity_difference", "difference_amount": 0})
        liquidity_data = await novig.run()

        league = list(filter_data.keys())[0]

        if not liquidity_data.get(league, []):
            print("No Liquidity Data Found")
            return None

        self.check_liquidity(liquidity_data)


if __name__ == "__main__":

    async def main():
        database = Database()
        filters = database.fetch_filters()

        mapping_group = defaultdict(dict)
        grouped_by_league = defaultdict(list)
        for filter in filters:
            league = filter.get("league")
            if league:
                selection_key = (league, filter.get("display_name"))
                grouped_by_league[league].append(filter)
                mapping_group[selection_key].update(filter)

        for index, league in enumerate(grouped_by_league):
            runner = Runner(
                database_instance=database,
                mapping_data=mapping_group
            )

            await runner.extract_liquidity(filter_data={league: grouped_by_league[league]})

    asyncio.run(main())
