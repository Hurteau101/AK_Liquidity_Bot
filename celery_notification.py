import asyncio
from datetime import timedelta
from celery import Celery
from Novig.novig import Novig
from Novig.novg_results import Results

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
    leagues = ["NFL"]
    novig_instance = Novig(leagues)
    asyncio.run(novig_instance.run())
