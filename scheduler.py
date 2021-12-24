import threading
import time
from typing import Dict, Callable

import schedule


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
        self.thread = None
        self.task_list = []

    def _run_schedule(self):
        for task in self.task_list:
            schedule.every().day.at(task.target_time).do(task.function, **task.args)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        self.thread = threading.Thread(target=self._run_schedule)
        self.thread.start()

    def add(self, task: Task):
        self.task_list.append(task)
