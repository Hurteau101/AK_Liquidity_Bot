import json

from novig import Novig
import asyncio

from ProcessManager import ProcessManager


class NovigSender:
    def __init__(self, filter_data, difference_amount, highest_order):
        self.filters = filter_data
        self.difference_amount = difference_amount
        self.highest_order = highest_order



    async def runner(self):
        total_and_difference_filter = {
            "filter_type": "total_and_difference",
            "difference_amount": self.difference_amount,
            "highest_order_amount": self.highest_order
        }

        novig = Novig(filters=self.filters, filter_amount_dict=total_and_difference_filter)
        return await novig.run()



if __name__ == "__main__":
    async def main():
        with open("nfl_filters.json", "r") as f:
            nfl_filters = json.load(f)
            nfl_mainlines = {"NFL": nfl_filters.get("NFL", {}).get("NFL_Mainlines")}
            nfl_props = {"NFL": nfl_filters.get("NFL", {}).get("NFL_Props")}

        with open("nba_filters.json", "r") as f:
            nba_data = json.load(f)
            nba_mainlines = {"NBA": nba_data.get("NBA", {}).get("NBA_Mainlines")}
            nba_props = {"NBA": nba_data.get("NBA", {}).get("NBA_Props")}


        nfl_bot_mainlines = NovigSender(filter_data=nfl_mainlines, difference_amount=4000, highest_order=5000)
        nfl_bot_prop = NovigSender(filter_data=nfl_props, difference_amount=4000, highest_order=3000)

        nba_bot_mainlines = NovigSender(filter_data=nba_mainlines, difference_amount=3000, highest_order=5000)
        nba_bot_prop = NovigSender(filter_data=nba_props, difference_amount=4000, highest_order=3000)

        # nfl_bot = NovigSender(filter_data=nfl_filters, difference_amount=4000, highest_order=3000)
        # nba_bot = NovigSender(filter_data=nba_filters, difference_amount=4000, highest_order=3000)

        nfl_mainline_data, nfl_prop_data, nba_mainline_data, nba_prop_data = await asyncio.gather(
            nfl_bot_mainlines.runner(),
            nfl_bot_prop.runner(),
            nba_bot_mainlines.runner(),
            nba_bot_prop.runner(),
        )

        nfl_mainline_manager = ProcessManager(redis_database=1, difference_amount=1000, league="NFL", market_type="mainlines")
        nfl_mainline_manager.manger(nfl_mainline_data["NFL"], "NFL")

        nfl_prop_manager = ProcessManager(redis_database=2, difference_amount=1000, league="NFL", market_type="props")
        nfl_prop_manager.manger(nfl_prop_data["NFL"], "NFL")

        nba_mainline_manager = ProcessManager(redis_database=3, difference_amount=1000, league="NBA",  market_type="mainlines")
        nba_mainline_manager.manger(nba_mainline_data["NBA"], "NBA")

        nba_prop_manager = ProcessManager(redis_database=4, difference_amount=1000, league="NBA", market_type="props")
        nba_prop_manager.manger(nba_prop_data["NBA"], "NBA")


        # nfl_manager = ProcessManager(redis_database=1, difference_amount=1000, league="NFL")
        # nfl_manager.manger(nfl_data["NFL"], "NFL")
        #
        # nba_manager = ProcessManager(redis_database=2, difference_amount=1000, league="NBA")
        # nba_manager.manger(nba_data["NBA"], "NBA")

    asyncio.run(main())


