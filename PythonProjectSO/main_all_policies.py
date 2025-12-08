# main_all_policies.py
import csv
import time
from helpers import load_input
from master import Master

INPUT_FILE = "example_input.json"   # ajuste se necessário
POLICIES = ["RR", "SJF", "PRIORITY"]  # políticas pedidas no PDF

def run_policy_once(servers, tasks, policy, realtime=False, seed=42):
    """
    Executa a simulação com a política escolhida e retorna o objeto Master
    (que contém completed_log, assigned_log, start/end times, etc).
    """
    print("\n" + "="*60)
    print(f"Iniciando simulação: {policy}")
    print("="*60)
    m = Master(
        servers=servers,
        tasks=tasks,
        policy=policy,
        arrival_mean=0,     # chegada imediata para comparação determinística
        seed=seed,
        realtime=realtime
    )
    m.run()
    return m

def write_task_csv(filename, records):
    """
    records: lista de dicts com campos:
      policy, task_id, worker_id, start, end, runtime, prioridade, tipo
    """
    keys = ["policy","task_id","worker_id","start","end","runtime","prioridade","tipo"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in keys})
    print(f"CSV detalhado por tarefa salvo em: {filename}")

def write_summary_csv(filename, summaries):
    keys = ["policy","num_tasks","avg_response","throughput","total_time"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for s in summaries:
            writer.writerow({k: s.get(k,"") for k in keys})
    print(f"CSV resumo por política salvo em: {filename}")

def summarize_master(master_obj, policy_name):
    """
    Extrai métricas e lista de registros por tarefa a partir do Master.
    Retorna (per_task_records, summary_dict)
    """
    per_task = []
    resp_times = []
    for rec in master_obj.completed_log:
        task_id = rec.get("task_id") or rec.get("task", {}).get("id")
        worker_id = rec.get("worker_id") or rec.get("worker")
        start = rec.get("start") or rec.get("task", {}).get("start_time")
        end = rec.get("end") or rec.get("time")
        runtime = rec.get("runtime") or (end - start if start and end else None)
        prioridade = rec.get("prioridade") or rec.get("task", {}).get("prioridade")
        tipo = rec.get("tipo") or rec.get("task", {}).get("tipo")

        per_task.append({
            "policy": policy_name,
            "task_id": task_id,
            "worker_id": worker_id,
            "start": start,
            "end": end,
            "runtime": runtime,
            "prioridade": prioridade,
            "tipo": tipo
        })
        if runtime is not None:
            resp_times.append(runtime)

    total_tasks = len(per_task)
    avg_resp = (sum(resp_times) / len(resp_times)) if resp_times else 0.0
    total_time = (master_obj.end_time - master_obj.start_time) if (master_obj.start_time and master_obj.end_time) else 0.0
    throughput = (len(resp_times) / total_time) if total_time > 0 else 0.0

    summary = {
        "policy": policy_name,
        "num_tasks": total_tasks,
        "avg_response": avg_resp,
        "throughput": throughput,
        "total_time": total_time
    }

    return per_task, summary

def main():
    data = load_input(INPUT_FILE)
    servers = data["servidores"]
    tasks = data["requisicoes"]

    all_task_records = []
    all_summaries = []

    for policy in POLICIES:
        m = run_policy_once(servers, tasks, policy, realtime=False, seed=42)
        per_task, summary = summarize_master(m, policy)
        all_task_records.extend(per_task)
        all_summaries.append(summary)

    # salvar CSV detalhado por tarefa
    ts = int(time.time())
    detail_csv = f"tasks_detail_{ts}.csv"
    summary_csv = f"policies_summary_{ts}.csv"
    write_task_csv(detail_csv, all_task_records)
    write_summary_csv(summary_csv, all_summaries)

    # imprimir tabela comparativa
    print("\n" + "="*80)
    print("COMPARAÇÃO ENTRE POLÍTICAS")
    print("="*80)
    for s in all_summaries:
        print(f"Política: {s['policy']}")
        print(f"  Tarefas processadas : {s['num_tasks']}")
        print(f"  Tempo total         : {s['total_time']:.3f}s")
        print(f"  Tempo médio resposta: {s['avg_response']:.3f}s")
        print(f"  Throughput          : {s['throughput']:.3f} tasks/s")
        print("-"*60)

    print("\nArquivos gerados:")
    print(" - Detalhes por tarefa:", detail_csv)
    print(" - Resumo políticas:   ", summary_csv)
    print("\nFim.")

if __name__ == "__main__":
    main()
