import asyncio
from datetime import timedelta
from celery import Celery
from Novig.novig import Novig

celery_app = Celery(
    "notify_user_celery",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
)

celery_app.conf.beat_schedule = {
    "send_notifications": {
        "task": "notification.notify_user",
        "schedule": timedelta(seconds=30),
    }
}

@celery_app.task(name="notification.notify_user")
def notify_user():
    leagues = ["NFL"]
    novig_instance = Novig(leagues)
    asyncio.run(novig_instance.run())





# celery -A notification worker --loglevel=info --pool=solo
# celery -A notification beat --loglevel=info
