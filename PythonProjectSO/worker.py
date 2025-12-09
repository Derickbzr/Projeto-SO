# worker.py
import time
import threading
import queue

def _worker_thread_loop(worker_id, internal_q, out_queue, capacity):
    while True:
        task = internal_q.get()
        if task is None:
            break

        t_start = time.time()
        out_queue.put({"type": "started", "task": task, "worker": worker_id, "time": t_start})

        # simulação CPU-bound proporcional
        simulate_cpu_work(
            seconds=task["tempo_exec"],
            peso_cpu=task.get("peso_cpu", 1),
            capacity=capacity
        )

        t_end = time.time()
        out_queue.put({"type": "done", "task": task, "worker": worker_id, "time": t_end})
        internal_q.task_done()


def worker_process(worker_id, capacity, in_queue, out_queue):
    """
    Processo worker: cria 'capacity' threads e mantém uma fila interna.
    - in_queue: multiprocessing.Queue onde Master envia comandos {"cmd":"run", "task":...} ou None para terminar
    - out_queue: multiprocessing.Queue usado para enviar eventos ao Master
    """
    internal_q = queue.Queue()
    threads = []
    for _ in range(max(1, capacity)):
        t = threading.Thread(target=_worker_thread_loop,
                             args=(worker_id, internal_q, out_queue, capacity),
                             daemon=True)
        t.start()
        threads.append(t)

    # Loop principal do processo: recebe mensagens vindas do Master
    try:
        while True:
            msg = in_queue.get()
            # None -> sinal de shutdown
            if msg is None:
                break
            if msg.get("cmd") == "run":
                task = msg["task"]
                # Coloca a tarefa na fila interna (as threads vão pegar quando disponíveis)
                internal_q.put(task)
            else:
                # Mensagem desconhecida — ignorar
                pass
    except KeyboardInterrupt:
        pass
    finally:
        # sinaliza shutdown para threads internas
        for _ in threads:
            internal_q.put(None)
        # espera threads terminarem
        for t in threads:
            t.join(timeout=2.0)
        out_queue.put({"type": "exiting", "worker": worker_id, "time": time.time()})

def simulate_cpu_work(seconds, peso_cpu, capacity):
        """
        Simula trabalho CPU-bound proporcional à capacidade do servidor e ao peso da tarefa.
        Quanto maior a capacidade do worker, mais processamento cabe no mesmo tempo.
        """
        end = time.time() + seconds

        # Escala o número de operações pelo peso da tarefa e pela capacidade do worker
        ops = int(50_000 * peso_cpu * capacity)

        while time.time() < end:
            x = 0
            # loop CPU-bound
            for i in range(ops):
                x += i * i

