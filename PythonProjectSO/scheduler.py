# scheduler.py
import heapq
from collections import deque

class Scheduler:
    def __init__(self, policy="RR"):
        self.policy = policy
        if policy == "RR":
            self.queue = deque()
        elif policy in ("SJF", "PRIORITY"):
            self.queue = []
        else:
            raise ValueError("Unknown policy: " + str(policy))

    def push(self, task):
        # task é dicionário com campos: id, prioridade, tempo_exec, arrival_time, ...
        if self.policy == "RR":
            self.queue.append(task)
        elif self.policy == "SJF":
            heapq.heappush(self.queue, (task["tempo_exec"], task["arrival_time"], task))
        elif self.policy == "PRIORITY":
            heapq.heappush(self.queue, (task["prioridade"], task["arrival_time"], task))

    def pop(self):
        if self.is_empty():
            return None
        if self.policy == "RR":
            return self.queue.popleft()
        return heapq.heappop(self.queue)[-1]

    def is_empty(self):
        if self.policy == "RR":
            return len(self.queue) == 0
        return len(self.queue) == 0

    def __len__(self):
        return len(self.queue)
