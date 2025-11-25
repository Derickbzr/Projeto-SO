# monitor.py
import time
import psutil
import threading
import os
import shutil


class SystemMonitor:
    def __init__(self, worker_procs, interval=0.5):
        """
        worker_procs: dict { worker_id: multiprocessing.Process }
        """
        self.worker_procs = worker_procs
        self.interval = interval
        self.running = False
        self.thread = None

        # histórico
        self.cpu_history = {wid: [] for wid in worker_procs}
        self.mem_history = {wid: [] for wid in worker_procs}

        # --- PRÉ-AQUECER psutil UMA VEZ POR PROCESSO ---
        for wid, proc in worker_procs.items():
            try:
                p = psutil.Process(proc.pid)
                p.cpu_percent(interval=None)
            except:
                pass

    def _clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _terminal_width(self):
        return shutil.get_terminal_size((80, 20)).columns

    def _run(self):
        self.running = True

        while self.running:
            self._clear()
            width = self._terminal_width()

            print("=" * width)
            print(" MONITORAMENTO EM TEMPO REAL (psutil + multiprocessing) ")
            print("=" * width)

            for wid, proc in self.worker_procs.items():
                try:
                    p = psutil.Process(proc.pid)

                    # medir sem resets
                    cpu = p.cpu_percent(interval=0.1)
                    mem = p.memory_info().rss / (1024 * 1024)
                    threads = p.num_threads()

                    self.cpu_history[wid].append(cpu)
                    self.mem_history[wid].append(mem)

                    print(
                        f"Worker {wid:02d} | "
                        f"CPU: {cpu:5.1f}% | RAM: {mem:6.1f} MB | Threads: {threads}"
                    )
                except psutil.NoSuchProcess:
                    print(f"Worker {wid} finalizado.")

            print("=" * width)
            print(f"[Atualizando a cada {self.interval}s]")
            print("=" * width)

            time.sleep(self.interval)

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def get_final_metrics(self):
        summary = {}
        for wid in self.cpu_history:
            cpu_avg = sum(self.cpu_history[wid]) / max(len(self.cpu_history[wid]), 1)
            mem_avg = sum(self.mem_history[wid]) / max(len(self.mem_history[wid]), 1)

            summary[wid] = {
                "cpu_avg": cpu_avg,
                "mem_avg": mem_avg
            }
        return summary
