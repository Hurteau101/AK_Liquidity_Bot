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
        with open("nfl_filters.json") as f:
            nfl_filters = json.load(f)

        with open("nba_filters.json") as f:
            nba_filters = json.load(f)

        nfl_bot = NovigSender(filter_data=nfl_filters, difference_amount=1000, highest_order=3000)
        nba_bot = NovigSender(filter_data=nba_filters, difference_amount=400, highest_order=1000)

        nfl_data, nba_data = await asyncio.gather(
            nfl_bot.runner(),
            nba_bot.runner()
        )

        nfl_manager = ProcessManager(redis_database=1, difference_amount=1000, league="NFL")
        nfl_manager.manger(nfl_data["NFL"], "NFL")

        nba_manager = ProcessManager(redis_database=2, difference_amount=1000, league="NBA")
        nba_manager.manger(nba_data["NBA"], "NBA")

    asyncio.run(main())


