# scheduler.py
import heapq
import itertools
from collections import deque

class Scheduler:
    def __init__(self, policy="RR"):
        self.policy = policy
        self.counter = itertools.count()   # contador para desempate

        if policy == "RR":
            self.queue = deque()
        elif policy in ("SJF", "PRIORITY"):
            self.queue = []
        else:
            raise ValueError("Unknown policy: " + str(policy))

    def push(self, task):
        """
        task: { id, tipo, prioridade, tempo_exec, arrival_time, ... }
        """
        if self.policy == "RR":
            self.queue.append(task)

        elif self.policy == "SJF":
            # ordenar por menor tempo_exec
            heapq.heappush(
                self.queue,
                (task["tempo_exec"], next(self.counter), task)
            )

        elif self.policy == "PRIORITY":
            # ordenar por menor prioridade numérica
            heapq.heappush(
                self.queue,
                (task["prioridade"], next(self.counter), task)
            )

    def pop(self):
        if self.is_empty():
            return None

        if self.policy == "RR":
            return self.queue.popleft()

        # para SJF e PRIORITY
        return heapq.heappop(self.queue)[-1]

    def is_empty(self):
        return len(self.queue) == 0

    def __len__(self):
        return len(self.queue)
