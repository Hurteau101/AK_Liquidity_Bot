import asyncio
from collections import defaultdict
from datetime import timedelta
from celery import Celery
from Database.database import Database
from novg_results import Results
from runner import Runner

celery_app = Celery(
    "notify_user_celery",
    broker="redis://localhost:6379/6",
    backend="redis://localhost:6379/6",
)


celery_app.conf.beat_schedule = {
    "send_notifications": {
        "task": "celery_notification.notify_user",
        "schedule": timedelta(seconds=30),
    },
    "update_results": {
        "task": "celery_notification.update_results",
        "schedule": timedelta(hours=12),
    }
}


@celery_app.task(name="celery_notification.update_results")
def update_results():
    results_instance = Results()
    results_instance.get_results()

@celery_app.task(name="celery_notification.notify_user")
def notify_user():
    asyncio.run(_notify_user_async())


async def _notify_user_async():
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

