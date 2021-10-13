import time
from threading import Timer, Thread


class TaskRunner(object):
    def __init__(self, wait_time, task_func, start=False, args=None, kwargs=None):
        self.wait_time = wait_time
        self.task_func = task_func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_running = False
        if start:
            self.start()

    def _run(self):
        while True:
            try:
                if not self.is_running:
                    return

                self.task_func(*self.args, **self.kwargs)

            except (KeyError, Exception) as e:
                print(f"Error running function {self.task_func}: \n {e}")

            time.sleep(self.wait_time)

    def start(self):
        if self.is_running:
            return

        t = Thread(target=self._run, daemon=True)
        self.is_running = True
        t.start()

    def stop(self):
        self.is_running = False
