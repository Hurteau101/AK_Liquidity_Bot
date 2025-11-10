import asyncio
import json
from datetime import timedelta
from celery import Celery
from Novig_Dir.novig_bot import NovigSender
from Novig_Dir.novg_results import Results
from ProcessManager import ProcessManager

celery_app = Celery(
    "notify_user_celery",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
)

celery_app.conf.beat_schedule = {
    "send_notifications": {
        "task": "celery_notification.notify_user",
        "schedule": timedelta(seconds=30),
    },
    "update_results": {
        "task": "celery_notification.update_results",
        "schedule": timedelta(hours=12),
    },
}

@celery_app.task(name="celery_notification.update_results")
def update_results():
    results_instance = Results()
    results_instance.get_results()

@celery_app.task(name="celery_notification.notify_user")
def notify_user():
    asyncio.run(_notify_user_async())


async def _notify_user_async():
    with open("Novig_Dir/nfl_filters.json") as f:
        nfl_filters = json.load(f)
        nfl_mainlines = {"NFL": nfl_filters.get("NFL", {}).get("NFL_Mainlines")}
        nfl_props = {"NFL": nfl_filters.get("NFL", {}).get("NFL_Props")}

    with open("Novig_Dir/nba_filters.json") as f:
        nba_data = json.load(f)
        nba_mainlines = {"NBA": nba_data.get("NBA", {}).get("NBA_Mainlines")}
        nba_props = {"NBA": nba_data.get("NBA", {}).get("NBA_Props")}

    nfl_bot_mainlines = NovigSender(filter_data=nfl_mainlines, difference_amount=4000, highest_order=5000)
    nfl_bot_prop = NovigSender(filter_data=nfl_props, difference_amount=3000, highest_order=2499)

    nba_bot_mainlines = NovigSender(filter_data=nba_mainlines, difference_amount=4000, highest_order=5000)
    nba_bot_prop = NovigSender(filter_data=nba_props, difference_amount=3000, highest_order=2499)

    nfl_mainline_data, nfl_prop_data, nba_mainline_data, nba_prop_data = await asyncio.gather(
        nfl_bot_mainlines.runner(),
        nfl_bot_prop.runner(),
        nba_bot_mainlines.runner(),
        nba_bot_prop.runner(),
    )

    nfl_mainline_manager = ProcessManager(redis_database=1, difference_amount=1000, league="NFL",
                                          market_type="mainlines")
    nfl_mainline_manager.manger(nfl_mainline_data["NFL"], "NFL")

    nfl_prop_manager = ProcessManager(redis_database=2, difference_amount=1000, league="NFL", market_type="props")
    nfl_prop_manager.manger(nfl_prop_data["NFL"], "NFL")

    nba_mainline_manager = ProcessManager(redis_database=3, difference_amount=1000, league="NBA",
                                          market_type="mainlines")
    nba_mainline_manager.manger(nba_mainline_data["NBA"], "NBA")

    nba_prop_manager = ProcessManager(redis_database=4, difference_amount=1000, league="NBA", market_type="props")
    nba_prop_manager.manger(nba_prop_data["NBA"], "NBA")

