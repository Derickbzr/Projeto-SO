📘 BSB Compute – Simulador de Orquestração de Servidores de IA

Este projeto é uma simulação funcional de um sistema distribuído de inferência baseado nos conceitos de:

Escalonamento de processos

Comunicação entre processos (IPC)

Balanceamento de carga

Execução paralela (multiprocessing)

Métricas de desempenho

Ele representa um orquestrador ("Master") que distribui tarefas para vários "Workers", imitando o comportamento de um cluster real utilizado por empresas como a BSB Compute.

📂 Arquitetura Geral
Master (Orquestrador)
 ├── Scheduler (RR, SJF, Prioridade)
 ├── Monitor (métricas)
 └── Workers (processos independentes)

Master

Recebe as requisições (arquivos ou geração dinâmica)

Seleciona qual Worker executará a tarefa

Envia tarefas via IPC (multiprocessing.Queue)

Coleta resultados

Calcula métricas

Workers

Representam servidores reais com capacidade limitada

Executam tarefas (simulação via sleep)

Retornam os resultados ao Master

Scheduler

Políticas suportadas:

RR – Round Robin

SJF – Shortest Job First

PRIORITY – prioridade numérica (1 = alta)

📄 Exemplo de Entrada (JSON)
{
  "servidores": [
    {"id": 1, "capacidade": 3},
    {"id": 2, "capacidade": 2},
    {"id": 3, "capacidade": 1}
  ],
  "requisicoes": [
    {"id": 101, "tipo": "visao_computacional", "prioridade": 1, "tempo_exec": 8},
    {"id": 102, "tipo": "nlp", "prioridade": 3, "tempo_exec": 3},
    {"id": 103, "tipo": "voz", "prioridade": 2, "tempo_exec": 5}
  ]
}

▶ Como Executar
python3 main.py --input exemplo.json --policy RR

Parâmetros opcionais:
Parâmetro	Descrição
--policy	RR, SJF, PRIORITY
--arrival-mean	Média de chegada de novas requisições
--seed	Semente aleatória
--save-csv	Salva métricas em metrics.csv
📊 Saída Esperada

Durante a simulação:

[00:01] Requisição 101 atribuída ao Servidor 1
[00:04] Servidor 1 concluiu Requisição 101


Ao final:

================ RESUMO FINAL ================
Tempo médio de resposta: 6.2s
Total concluídas: 15
Throughput: 0.97 tarefas/segundo
==============================================

🧪 Testes Recomendados

Assim que os arquivos .py forem disponibilizados fisicamente, os testes podem ser executados:

📌 Teste 1 — Round Robin
python3 main.py --input example.json --policy RR


Saída esperada:

distribuição circular entre servidores

📌 Teste 2 — SJF
python3 main.py --input example.json --policy SJF


Saída esperada:

tarefas curtas sendo executadas primeiro

📌 Teste 3 — Prioridade
python3 main.py --input example.json --policy PRIORITY


Saída esperada:

requisições prioridade 1 sempre antes das demais

📦 Estrutura Final do Projeto
PythonProjectSO/
 ├── main.py
 ├── master.py
 ├── scheduler.py
 ├── worker.py
 ├── monitor.py
 ├── helpers.py
 ├── example_input.json
 ├── README.md
