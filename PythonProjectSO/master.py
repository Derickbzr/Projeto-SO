# master.py
import time
import random
import multiprocessing as mp
from collections import defaultdict, deque

from scheduler import Scheduler
from worker import worker_process

class WorkerInfo:
    def __init__(self, wid, capacity):
        self.id = wid
        self.capacity = capacity
        self.inflight = 0  # inclui tarefas em execução + enfileiradas no worker
        self.executed = 0

class Master:
    def __init__(self, servers_cfg, tasks_list, policy="RR", arrival_mean=1.0, seed=42, realtime=True):
        self.servers_cfg = servers_cfg
        self.tasks_list = tasks_list[:]  # copia
        self.policy = policy
        self.arrival_mean = arrival_mean
        self.realtime = realtime
        random.seed(seed)

        self.scheduler = Scheduler(policy)
        self.task_meta = {}
        self.metrics = {"response_times": [], "wait_times": [], "task_count": 0}

        self.worker_out = mp.Queue()
        self.worker_in = {}
        self.workers = {}
        self.worker_infos = {}

        # inflate initial worker infos from cfg
        for s in self.servers_cfg:
            wid, cap = s["id"], s["capacidade"]
            self.worker_infos[wid] = WorkerInfo(wid, cap)

    def start_workers(self):
        for s in self.servers_cfg:
            wid, cap = s["id"], s["capacidade"]
            q = mp.Queue()
            p = mp.Process(target=worker_process, args=(wid, cap, q, self.worker_out), daemon=True)
            p.start()
            self.worker_in[wid] = q
            self.workers[wid] = p

    def stop_workers(self):
        # envia sinal de término para todos workers
        for q in self.worker_in.values():
            q.put(None)
        # espera finalização
        for p in self.workers.values():
            p.join(timeout=2.0)

    def log(self, text):
        t = time.time() - self.global_time_start
        stamp = f"[{t:06.2f}]"
        line = f"{stamp} {text}"
        print(line)

    def find_worker_with_free_slot(self):
        # retorna wid com (capacity - inflight) > 0, preferindo maior folga
        best = None
        best_free = -999
        for wid, info in self.worker_infos.items():
            free = info.capacity - info.inflight
            if free > best_free:
                best_free = free
                best = wid
        if best_free <= 0:
            return None
        return best

    def assign_task_to_worker(self, task, wid):
        # envia para worker e atualiza inflight localmente (conta também filas internas)
        self.worker_in[wid].put({"cmd":"run", "task": task})
        info = self.worker_infos[wid]
        info.inflight += 1
        info.executed += 1
        self.task_meta[task["id"]]["assigned_time"] = time.time()
        self.metrics["task_count"] += 1
        self.log(f"Requisição {task['id']} (prio {task['prioridade']}, t={task['tempo_exec']}) atribuída ao Servidor {wid}")

    def run(self, max_time=300):
        self.global_time_start = time.time()
        self.start_workers()

        # preparar cronograma de chegadas
        arrivals = []
        t = 0.0
        for task in self.tasks_list:
            ia = random.expovariate(1.0 / self.arrival_mean) if self.realtime else 0.0
            t += ia
            arrivals.append((t, task))
        arrivals.sort(key=lambda x: x[0])
        pending_arrivals = deque(arrivals)

        inflight_counts = {wid: 0 for wid in self.worker_infos}  # redundante, mantemos em worker_infos também

        sim_running = True
        while sim_running:
            now = time.time() - self.global_time_start

            # 1) injetar chegadas
            while pending_arrivals and pending_arrivals[0][0] <= now:
                _, tsk = pending_arrivals.popleft()
                self.task_meta[tsk["id"]] = {"arrival_time": time.time()}
                # push para scheduler
                self.scheduler.push({
                    "id": tsk["id"],
                    "tipo": tsk.get("tipo",""),
                    "prioridade": tsk["prioridade"],
                    "tempo_exec": tsk["tempo_exec"],
                    "arrival_time": time.time()
                })
                self.log(f"Requisição {tsk['id']} chegou (prio {tsk['prioridade']}, t={tsk['tempo_exec']})")

            # 2) tentar agendar (respeitando capacidade)
            while not self.scheduler.is_empty():
                wid = self.find_worker_with_free_slot()
                if wid is None:
                    break
                task = self.scheduler.pop()
                self.assign_task_to_worker(task, wid)

            # 3) processar mensagens dos workers (non-blocking)
            while True:
                try:
                    msg = self.worker_out.get_nowait()
                except:
                    break
                if msg["type"] == "started":
                    tid = msg["task"]["id"]
                    self.task_meta[tid]["start_time"] = msg["time"]
                    self.log(f"Servidor {msg['worker']} iniciou Requisição {tid}")
                elif msg["type"] == "done":
                    tid = msg["task"]["id"]
                    wid = msg["worker"]
                    # reduzir inflight do worker (tarefa finalizada)
                    self.worker_infos[wid].inflight = max(0, self.worker_infos[wid].inflight - 1)
                    self.task_meta[tid]["end_time"] = msg["time"]

                    meta = self.task_meta[tid]
                    response = meta["end_time"] - meta["arrival_time"]
                    wait = meta["start_time"] - meta["arrival_time"]
                    self.metrics["response_times"].append(response)
                    self.metrics["wait_times"].append(wait)
                    self.log(f"Servidor {wid} concluiu Requisição {tid} (resp {response:.2f}s, wait {wait:.2f}s)")
                elif msg["type"] == "pong":
                    pass
                elif msg["type"] == "exiting":
                    self.log(f"Worker {msg['worker']} exiting")

            # 4) condição de parada
            all_arrivals_done = (not pending_arrivals)
            all_queues_empty = self.scheduler.is_empty() and all(info.inflight == 0 for info in self.worker_infos.values())
            if all_arrivals_done and all_queues_empty:
                sim_running = False

            if (time.time() - self.global_time_start) > max_time:
                self.log("Tempo máximo de simulação atingido.")
                break

            time.sleep(0.01)

        # finaliza workers
        self.stop_workers()
        self.finish_time = time.time()
        self.sim_duration = self.finish_time - self.global_time_start

    def print_summary(self):
        print("\n" + "-"*40)
        print("Resumo Final:")
        if self.metrics["response_times"]:
            avg_resp = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            avg_wait = sum(self.metrics["wait_times"]) / len(self.metrics["wait_times"])
        else:
            avg_resp = avg_wait = 0.0
        throughput = len(self.metrics["response_times"]) / max(self.sim_duration, 1e-6)
        print(f"Tempo médio de resposta: {avg_resp:.2f}s")
        print(f"Tempo médio de espera: {avg_wait:.2f}s")
        print(f"Throughput: {throughput:.2f} tarefas/s")
        print(f"Total de tarefas processadas: {len(self.metrics['response_times'])}")
        print(f"Duração da simulação (wall): {self.sim_duration:.2f}s")
        print("-"*40)
        for wid, info in self.worker_infos.items():
            print(f"Servidor {wid}: capacidade={info.capacity}, tarefas_executadas={info.executed}, inflight_final={info.inflight}")
        print("-"*40)
