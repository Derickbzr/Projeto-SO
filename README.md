# 🖥️ Projeto SO – Simulador de Escalonamento com Workers Paralelos

Este projeto implementa um simulador de ambiente distribuído onde tarefas chegam ao sistema,
são organizadas em um escalonador e distribuídas entre workers paralelos seguindo diferentes
políticas de escalonamento.

Cada worker possui capacidade própria, executa tarefas em paralelo usando threads internas e
simula consumo de CPU real proporcional à sua capacidade. O sistema também oferece
monitoramento em tempo real via psutil, coleta de métricas e relatório final da execução.

---

## 🚀 Funcionalidades

### ✔ Escalonamento de tarefas
- Round-Robin (**RR**)
- Shortest Job First (**SJF**)
- Prioridade (**PRIORITY**)
- Chegada de tarefas seguindo distribuição exponencial

### ✔ Workers paralelos
- Cada worker é um processo separado
- Capacidade configurável
- Execução paralela via múltiplas threads internas
- Simulação de carga CPU-bound real

### ✔ Monitoramento em tempo real
- Uso de CPU e RAM por worker (psutil)
- Número de threads
- Atualização contínua no terminal

### ✔ Métricas finais
- Tempo médio de resposta
- Tempo médio de espera
- Throughput
- Tarefas por worker
- Uso médio de CPU por worker
- Uso médio de CPU do sistema

---
