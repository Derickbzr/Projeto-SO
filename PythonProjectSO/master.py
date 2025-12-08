# master.py
import multiprocessing as mp
import time
import random
import argparse
import queue
from scheduler import Scheduler
from monitor import SystemMonitor
from helpers import load_input
from worker import worker_process

class Master:
    def __init__(self, servers, tasks, policy="RR", arrival_mean=1.0, seed=42, realtime=True, monitor_interval=0.8):
        random.seed(seed)
        # servidores: lista de dicts {"id":int, "capacidade": int}
        self.servers_meta = {s["id"]: {"id": s["id"], "capacity": int(s["capacidade"])} for s in servers}
        self.policy = policy
        self.scheduler = Scheduler(policy=policy)
        self.raw_tasks = list(tasks)  # tarefas aguardando chegada
        self.arrival_mean = arrival_mean
        self.realtime = realtime

        # filas de comunicação
        self.in_queues = {}   # server_id -> mp.Queue (Master => Worker)
        self.out_queue = mp.Queue()  # todos workers escrevem aqui (events)

        # processos workers
        self.worker_procs = {}  # server_id -> mp.Process

        # per-worker bookkeeping for pull-like behavior
        self.sent_pending = {}   # tasks sent but not yet "started" (count)
        self.in_flight = {}      # tasks started and not yet done
        self.capacity = {}       # capacity per worker

        # logs / metrics
        self.assigned_log = []   # (timestamp, task_id, server_id)
        self.completed_log = []  # result events (dict with start,end,runtime,...)
        self.start_time = None
        self.end_time = None

        # monitor
        self.monitor = None
        self.monitor_interval = monitor_interval

        # init workers bookkeeping
        for sid, meta in self.servers_meta.items():
            self.sent_pending[sid] = 0
            self.in_flight[sid] = 0
            self.capacity[sid] = meta["capacity"]

    # -------------------------
    # worker lifecycle
    # -------------------------
    def spawn_workers(self):
        for sid, meta in self.servers_meta.items():
            in_q = mp.Queue()
            self.in_queues[sid] = in_q
            p = mp.Process(target=worker_process, args=(sid, meta["capacity"], in_q, self.out_queue), daemon=True)
            p.start()
            self.worker_procs[sid] = p
            # small sleep to avoid race of processes starting at same instant
            time.sleep(0.02)

    def stop_workers(self):
        # send shutdown (None) to each worker's in_queue and join
        for sid, q in self.in_queues.items():
            try:
                q.put(None)
            except Exception:
                pass
        for sid, p in self.worker_procs.items():
            try:
                p.join(timeout=2.0)
            except Exception:
                pass

    # -------------------------
    # scheduler / dispatch
    # -------------------------
    def dispatch_if_possible(self):
        """
        Tenta enviar tarefas do scheduler para workers que tenham (in_flight + sent_pending) < capacity.
        Mantemos a propriedade PULL-like: só enviamos até preencher a capacidade.
        """
        # tentar para cada servidor enquanto existirem tarefas
        # heurística: iterar servidores ordenados por carga (prefira menos ocupados)
        server_ids = sorted(self.servers_meta.keys(), key=lambda s: (self.in_flight[s] + self.sent_pending[s]) / max(1, self.capacity[s]))
        dispatched = 0

        for sid in server_ids:
            # enquanto houver espaço e tarefas no scheduler
            while (self.in_flight[sid] + self.sent_pending[sid]) < self.capacity[sid] and len(self.scheduler) > 0:
                task = self.scheduler.pop()
                if task is None:
                    break
                # send to worker
                msg = {"cmd": "run", "task": task}
                try:
                    self.in_queues[sid].put(msg)
                    self.sent_pending[sid] += 1
                    dispatched += 1
                    self.assigned_log.append((time.time(), task["id"], sid))
                    print(f"[{self._fmt_time()}] Requisição {task['id']} (P{task.get('prioridade')}) atribuída ao Servidor {sid}")
                except Exception as e:
                    # se falhar, re-push na scheduler para tentar depois
                    print("Falha ao enviar tarefa ao worker:", e)
                    self.scheduler.push(task)
                    break
        return dispatched

    # -------------------------
    # main loop
    # -------------------------
    def run(self):
        self.start_time = time.time()
        # spawn workers
        self.spawn_workers()

        # iniciar monitor se realtime
        if self.realtime:
            try:
                self.monitor = SystemMonitor(self.worker_procs, interval=self.monitor_interval)
                self.monitor.start()
            except Exception as e:
                print("Falha ao iniciar monitor:", e)
                self.monitor = None

        # preparar chegadas
        arrivals = list(self.raw_tasks)
        total_tasks = len(arrivals)
        waiting_count = 0
        if not self.realtime:
            # chegada imediata: empilhar tudo na scheduler
            for t in arrivals:
                # adicionar timestamp de arrival (opcional)
                t["arrival_time"] = time.time()
                self.scheduler.push(t)
            arrivals = []
        else:
            # primeiro chegada
            next_arrival_at = time.time() + max(0.0001, random.expovariate(1.0 / max(1e-6, self.arrival_mean)))

        completed = 0
        last_balance_check = time.time()

        try:
            # logo após spawn, tentar preencher inicialmente as capacidades (se tasks já chegaram)
            self.dispatch_if_possible()

            while completed < total_tasks:
                now = time.time()
                # process arrivals
                if self.realtime and arrivals and now >= next_arrival_at:
                    t = arrivals.pop(0)
                    t["arrival_time"] = now
                    self.scheduler.push(t)
                    print(f"[{self._fmt_time()}] Nova requisição {t['id']} chegou (P{t.get('prioridade')})")
                    # schedule next
                    inter = random.expovariate(1.0 / max(1e-6, self.arrival_mean))
                    next_arrival_at = now + inter

                # dispatch tasks where possible
                if len(self.scheduler) > 0:
                    self.dispatch_if_possible()

                # process events from workers (non-blocking)
                try:
                    while True:
                        ev = self.out_queue.get_nowait()
                        self._handle_event(ev)
                        # count completions
                        if isinstance(ev, dict) and ev.get("type") == "done":
                            completed += 1
                except queue.Empty:
                    pass
                except Exception:
                    # mp.Queue may raise different Empty; try safe get with timeout 0
                    try:
                        ev = self.out_queue.get(timeout=0)
                        if ev is not None:
                            self._handle_event(ev)
                            if isinstance(ev, dict) and ev.get("type") == "done":
                                completed += 1
                    except Exception:
                        pass

                # periodic balancing / migration heuristics (simple)
                if time.time() - last_balance_check > 2.0:
                    self._balance_check()
                    last_balance_check = time.time()

                time.sleep(0.02)
        finally:
            self.end_time = time.time()
            # teardown
            self.stop_workers()
            if self.monitor:
                self.monitor.stop()
                self.monitor_summary = self.monitor.get_final_metrics()
            else:
                self.monitor_summary = {}

    def _handle_event(self, ev):
        """
        Eventos esperados do worker:
          - {"type":"started","task":..., "worker":id, "time":t}
          - {"type":"done","task":..., "worker":id, "time":t}
          - {"type":"pong","worker":id, "time":t}
          - {"type":"exiting","worker":id, "time":t}
        """
        if not isinstance(ev, dict):
            return

        etype = ev.get("type")
        wid = ev.get("worker")
        if etype == "started":
            # task começou: converte sent_pending -> in_flight
            if self.sent_pending.get(wid, 0) > 0:
                self.sent_pending[wid] -= 1
            self.in_flight[wid] += 1
            # log optional
            # print(f"[{self._fmt_time()}] Worker {wid} iniciou task {ev['task']['id']}")
        elif etype == "done":
            # tarefa finalizada: decrementar in_flight
            if self.in_flight.get(wid, 0) > 0:
                self.in_flight[wid] -= 1
            # registrar resultado para métricas
            task = ev.get("task", {})
            t_end = ev.get("time", time.time())
            # tentar montar um registro de start/end/runtime se possível
            record = {
                "task_id": task.get("id"),
                "worker_id": wid,
                "start": task.get("start_time", None),
                "end": t_end,
                "runtime": ev.get("time", None) - task.get("start_time", ev.get("time", None)) if task.get("start_time") else None,
                "prioridade": task.get("prioridade"),
                "tipo": task.get("tipo")
            }
            self.completed_log.append(record)
            print(f"[{self._fmt_time()}] Servidor {wid} concluiu Requisição {task.get('id')}")
            # após done, tentar dispatch imediato (worker liberou slot)
            self.dispatch_if_possible()
        elif etype == "pong":
            # worker respondeu a ping
            pass
        elif etype == "exiting":
            print(f"[{self._fmt_time()}] Worker {wid} exiting")
        else:
            # evento desconhecido — ignora
            pass

    def _balance_check(self):
        """
        Heurística simples: se algum worker está ocioso e existe backlog, priorizar envio para ele.
        Como todas as tasks estão no scheduler central, 'migração' é natural — o master decide para quem enviar.
        """
        # apenas uma nota/print do estado atual
        loads = {sid: self.in_flight[sid] + self.sent_pending[sid] for sid in self.servers_meta}
        print(f"[{self._fmt_time()}] Estado cargas (in_flight+pending): {loads}")

    # -------------------------
    # summary
    # -------------------------
    def print_summary(self):
        total = len(self.completed_log)
        if total == 0:
            print("Nenhuma tarefa completada.")
            return

        # calcular tempos de resposta
        resp_times = []
        for r in self.completed_log:
            start = r.get("start")
            end = r.get("end")
            if start and end:
                resp_times.append(end - start)
            else:
                # fallback
                rt = r.get("runtime")
                if rt:
                    resp_times.append(rt)

        avg_resp = sum(resp_times) / max(1, len(resp_times))
        total_time = (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0
        throughput = len(resp_times) / max(total_time, 1e-6)

        print("\n" + "-" * 60)
        print("RESUMO FINAL")
        print("-" * 60)
        print(f"Tarefas processadas: {len(resp_times)}")
        print(f"Tempo total de simulação: {total_time:.2f}s")
        print(f"Tempo médio de resposta: {avg_resp:.2f}s")
        print(f"Throughput: {throughput:.2f} tarefas/s")

        print("-" * 60)
        if hasattr(self, "monitor_summary") and self.monitor_summary:
            print("Utilização média dos Workers:")
            for wid, m in self.monitor_summary.items():
                print(f"  Worker {wid}: CPU {m['cpu_avg']:.1f}% | Mem {m['mem_avg']:.1f} MB")
        print("-" * 60)

    # -------------------------
    def _fmt_time(self):
        t = time.time() - (self.start_time or time.time())
        mm = int(t // 60)
        ss = int(t % 60)
        return f"{mm:02d}:{ss:02d}"
