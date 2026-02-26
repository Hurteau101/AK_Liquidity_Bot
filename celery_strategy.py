from datetime import timedelta
from celery import Celery
from Strategy.strategy_checker import run_strategy_check

celery_app = Celery(
    "strategy_celery",
    broker="redis://localhost:6379/7",
    backend="redis://localhost:6379/7",
)

celery_app.conf.beat_schedule = {
    "run_strategy_checker": {
        "task": "strategy.run_checker",
        "schedule": timedelta(seconds=60),
    },
}

@celery_app.task(name="strategy.run_checker")
def run_strategy_checker():
    run_strategy_check()