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
async def notify_user():
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
