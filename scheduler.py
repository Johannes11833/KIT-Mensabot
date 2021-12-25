import atexit
import datetime
from typing import Dict, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class Task:
    target_time: str
    function: Callable
    args: Dict

    def __init__(self, target_time: str, function: Callable, args: Dict = None) -> None:
        super().__init__()

        self.target_time = target_time
        self.function = function
        self.args = args if args is not None else {}


class TimeScheduler:

    def __init__(self):
        self.task_list = []

    def start(self):
        scheduler = BackgroundScheduler()

        for task in self.task_list:
            t = datetime.time.fromisoformat(task.target_time)
            trigger = CronTrigger(hour=t.hour, minute=t.minute, second=t.second)
            scheduler.add_job(func=task.function, trigger=trigger)

        scheduler.start()

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())

    def add(self, task: Task):
        self.task_list.append(task)
