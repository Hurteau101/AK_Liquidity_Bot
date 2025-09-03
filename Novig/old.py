import asyncio
import json
import os.path
from collections import defaultdict
from dataclasses import asdict
from models import Player, Orders, GameDetails
import aiohttp

from Novig.novig_api import NovigAPI


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
        return league, results

    async def fetch_and_filter(self, session, event_id, league):
        """Fetch market data for a specific event and filter it based on the league."""
        market_data = await self.novig_api.query_caller(session, "market", event_id=event_id)
        # return market_data
        market_data = self._extract_data(market_data, league)
        grouped_data = self.group_by_market(market_data)
        return self._filter_data(grouped_data)
        # return self._filter_data(market_data, league)

    def group_by_market(self, players):
        grouped = defaultdict(list)
        for player in players:
            grouped[player.main_market_description].append(player)
        return grouped

    def _get_highest_order(self, orders):
        higest_order = max(orders, key=lambda order: order.liquidity_left)
        for order in orders:
            order.is_highest_order = (order == higest_order)

        return orders

    def _filter_data(self, market_data):
        for market_desc, players in market_data.items():  # each key is a market string
            for player in players:  # each value is a list of Player dataclasses
                player.orders = self._get_highest_order(player.orders)
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
                        main_market_description=key_market_description,
                        orders=[
                            Orders(
                                outcome_id=outcome.get("id"),
                                qty=order.get("qty"),
                                decimal_price=order.get("price"),
                                original_qty=order.get("originalQty"),
                                created_at=order.get("created_at"),
                                american_price=self.price_to_american(order.get("price")),
                                total_win=order.get("qty") / 100,
                                total_risk=order.get("price") * (order.get("qty") / 100),
                                liquidity_left=self.calculate_liquidity(order.get("qty"), order.get("price"))
                            )

                            for order in outcome.get("orders", [])
                            if order.get("status") == "OPEN"
                        ],
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

    # def deserailize_for_json(self, data, raw=False):
    #     """Convert the data to a format suitable for JSON serialization."""
    #     return {
    #         league: [asdict(player) for sublist in league_data for player in sublist]
    #         for league, league_data in data.items()
    #     }

    def deserailize_for_json(self, data, raw=False):
        output = {}

        for league, league_data in data.items():
            league_grouped = defaultdict(list)

            # league_data is a list of grouped dicts (one per event)
            for grouped in league_data:
                for market_desc, players in grouped.items():
                    league_grouped[market_desc].extend(asdict(p) for p in players)

            output[league] = dict(league_grouped)

        return output

    async def run(self):
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *(self.fetch_data(session, league) for league in self.league_list)
            )
            data_by_league = dict(results)

            # with open("new_novig_2_data.json", "w") as file:
            #     json.dump(data_by_league, file, indent=4)

            print(data_by_league)

            with open("final_data2.json", "w") as file:
                json.dump(self.deserailize_for_json(data_by_league), file, indent=4)


if __name__ == "__main__":
    leagues = ["NFL"]
    novig_instance = Novig(leagues)
    asyncio.run(novig_instance.run())