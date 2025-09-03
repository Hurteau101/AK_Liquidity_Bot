import asyncio
import json
import os.path
from collections import defaultdict
from dataclasses import asdict
from models import Player, Orders, GameDetails, LiquidityData
import aiohttp

from Novig.novig_api import NovigAPI
from redis_manager import RedisManager


class Novig:
    def __init__(self, league_list: list):
        self.league_list = league_list
        self.novig_api = NovigAPI()
        self.filters = Novig.load_filters()

    @staticmethod
    def load_filters():
        # Load league and stat filters from JSON files
        script_dir = os.path.dirname((os.path.abspath(__file__)))
        filter_path = os.path.join(script_dir, 'filters.json')

        filter_path = os.path.abspath(filter_path)

        with open(filter_path, 'r') as f:
            filter_data = json.load(f)

        return filter_data

    async def fetch_data(self, session, league):
        """Fetch data for a specific league and filter it based on the league's events."""
        league_ids = self.get_league_ids(await self.novig_api.query_caller(session, "league", league=league))
        tasks = [self.fetch_and_filter(session, event_id, league) for event_id in league_ids]
        results = await asyncio.gather(*tasks)

        flat_results = [market for sublist in results for market in sublist]

        return league, flat_results

    async def fetch_and_filter(self, session, event_id, league):
        """Fetch market data for a specific event and filter it based on the league."""
        market_data = await self.novig_api.query_caller(session, "market", event_id=event_id)
        market_data = self._extract_data(market_data, league)
        filtered_data = self._group_filter(market_data)
        return self._conditional_filter(filtered_data, filter_type="compare_difference", amount=3000)

        # return filtered_data
        # return market_data_change
        # return market_data

        # print(market_data)

    def _group_filter(self, market_data):
        result = defaultdict(lambda: {"liquidity": {}, "additional_data": None})

        for entry in market_data:
            market_description = entry.key_name
            side = entry.liquidity_data.highest_order["side"]

            result[market_description]["liquidity"][side] = asdict(entry.liquidity_data)

            result[market_description]["additional_data"] = {
                "player_name": entry.player_name,
                "stat_type": entry.stat_type,
                "line": entry.line,
                "game_title": entry.game_details.game_title,
                "game_start_time": entry.game_details.game_start_time,
            }

        return [
            {
                "key_name": market,
                "liquidity": data["liquidity"],
                "additional_data": data["additional_data"],
            }
            for market, data in result.items()
        ]

    def _difference_filter(self, difference_amount, market_data):
        # Filter markets where the difference between over and under liquidity meets or exceeds the specified amount
        results = []

        for data in market_data:
            over_liquidity_amount = (
                data.get("liquidity", {})
                .get("over", {})
                .get("highest_order", {})
                .get("total_liquidity", 0)
            )
            under_liquidity_amount = (
                data.get("liquidity", {})
                .get("under", {})
                .get("highest_order", {})
                .get("total_liquidity", 0)
            )

            liqudity_difference = round(abs(over_liquidity_amount - under_liquidity_amount),2)

            if liqudity_difference >= difference_amount:
                data["liqudity_difference"] = liqudity_difference
                results.append(data)

        return results

    def _conditional_filter(self, market_data, filter_type, amount=None):
        filters = {
            "compare_difference": self._difference_filter,
        }

        if filter_type not in filters:
            raise ValueError(f"Invalid filter type: {filter_type}")

        filter_func = filters[filter_type]

        if filter_type == "compare_difference":
            if amount is None:
                raise ValueError("compare_difference filter requires an 'amount'")
            return filter_func(amount, market_data)

        # fallback: return unfiltered
        return market_data



    def _map_data(self, market_name, league):
        for stat in self.filters.get(league, []):
            if stat.get("raw_name") and stat.get("raw_name", "").lower() == market_name.lower():
                return {
                    "valid": bool(stat.get("active")),
                    "stat_type": stat.get("display_name"),
                } if stat.get("active") else {"valid": False, "stat_type": market_name}

        return {"valid": False, "stat_type": market_name}


    @staticmethod
    def price_to_american(price: float) -> int:
        if price >= 1 or price <= 0:
            raise ValueError("Price must be between 0 and 1 (exclusive).")

        if price >= 0.5:
            odds = - (price / (1 - price)) * 100
        else:
            odds = ((1 - price) / price) * 100

        return int(round(odds))

    @staticmethod
    def calculate_liquidity(qty, price):
        return (1-price) * (qty / 100)

    def _get_highest_order(self, orders, direction_description, link_id):
        if not orders:
            return None

        highest = max(orders, key=lambda o: o["qty"] * o["price"])
        total_liquidity = sum(self.calculate_liquidity(order.get("qty"), order.get("price")) for order in orders)
        total_qty = sum(order.get("qty", 0) for order in orders)
        weighted_avg_price = sum(
            order.get("price", 0) * order.get("qty", 0) for order in orders
        ) / total_qty

        side = "over" if "over" in direction_description.lower() else "under"

        return {
            "total_win": round(highest["qty"] / 100,2),
            "total_risk": round(highest["price"] * (highest["qty"] / 100), 2),
            "liquidity_left": round(self.calculate_liquidity(highest["qty"], highest["price"]), 2),
            "american_price": self.price_to_american(highest["price"]),
            "total_liquidity": round(total_liquidity, 2),
            "cost_avg_odds": round(self.price_to_american(weighted_avg_price), 2),
            "side": side,
            "link":f"https://novig.onelink.me/JHQQ/events/{link_id}"
        }

    def _get_line(self, description):
        keywords = {"over", "under"}  # set is faster for membership checks
        split = next((word for word in description.lower().split() if word not in keywords), None)
        return split


    def _extract_data(self, market_data, league):
        market_data_list = []

        for event in market_data.get("data").get("event", []):
            for market in event.get("markets", []):
                if len(market.get("outcomes", [])) <= 0:
                    continue

                key_market_description = market.get("description", "")

                if len(market.get("description").split(" ")) == 1:
                    market_name = "Moneyline"
                else:
                    market_name = market.get("description", "").lower().split(" ")[-1]


                market_data_list.extend([
                    Player(
                        player_name=market.get("player", {}).get("full_name") if market.get("player") else None,
                        stat_type=self._map_data(market_name, league).get("stat_type"),
                        bet_info=outcome.get("description").title() if outcome.get("description") else None,
                        line=self._get_line(outcome.get("description")) if outcome.get("description") else None,
                        key_name=key_market_description,
                        orders=[
                            Orders(
                                outcome_id=outcome.get("id"),
                                qty=order.get("qty"),
                                decimal_price=order.get("price"),
                                original_qty=order.get("originalQty"),
                                created_at=order.get("created_at"),
                                american_price=self.price_to_american(order.get("price")),
                                total_win=round(order.get("qty") / 100,2),
                                total_risk=round(order.get("price") * (order.get("qty") / 100), 2),
                                liquidity_left=round(self.calculate_liquidity(order.get("qty"), order.get("price")), 2)
                            )

                            for order in outcome.get("orders", [])
                            if order.get("status") == "OPEN"
                        ],
                        liquidity_data=LiquidityData(
                            highest_order=self._get_highest_order(outcome.get("orders", []), outcome.get("description"), outcome.get("id"))
                        ),
                        game_details=GameDetails(
                            game_title=event.get("description"),
                            game_start_time=event.get("game", {}).get("scheduled_start")
                        )
                    )
                    for outcome in market.get("outcomes", [])
                    if any(order.get("status") == "OPEN" for order in outcome.get("orders", [])) and self._map_data(market_name, league).get("valid")
                ])
        return market_data_list



    def get_league_ids(self, league_info):
        """Get all the league IDs for a given league that are scheduled within the next 24 hours."""
        return [
            league_id
            for league in (league_info.get("data", {}).get("event", []))
            # if (scheduled := league.get("game", {}).get("scheduled_start")) and self.compare_dates(scheduled) ## Uncommented after testing
            if (league_id := league.get("id"))
        ]

    def deserailize_for_json(self, data, raw=False):
        """Convert the data to a format suitable for JSON serialization."""
        if raw:
            # keep full Player dataclasses expanded
            return {
                league: [asdict(player) for sublist in league_data for player in sublist]
                for league, league_data in data.items()
            }
        else:
            # already dicts from _discord_filter
            return {
                league: [player for sublist in league_data for player in sublist]
                for league, league_data in data.items()
            }

    async def run(self):
        redis = RedisManager()

        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *(self.fetch_data(session, league) for league in self.league_list)
            )
            data_by_league = dict(results)

            if data_by_league:
                for league, player_data in data_by_league.items():
                    if player_data:
                        redis.manger(player_data, league)


            # with open("final.json", "w") as file:
            #     json.dump(data_by_league, file, indent=4)

            # print(data_by_league)
            # #
            # with open("final_data3.json", "w") as file:
            #     json.dump(self.deserailize_for_json(data_by_league, raw=True), file, indent=4)


if __name__ == "__main__":
    leagues = ["NFL"]
    novig_instance = Novig(leagues)
    asyncio.run(novig_instance.run())