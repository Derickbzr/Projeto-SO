# Projeto de Sistema Operacional — Escalonamento de Processos

Este projeto implementa um simulador de escalonamento de processos em C, seguindo rigorosamente o enunciado fornecido.  
Foram implementados:

- **FCFS (First Come, First Served)**
- **Round Robin**
- **SJF com preempção (Shortest Job First — Preemptivo)**

Também foram criadas estruturas de PCB, gerenciador de filas, simulações de tempo, controle de processo atual, estatísticas e testes completos.

---

## 📁 Estrutura do Projeto

```
Projeto-SO/
│
├── inc/
│   ├── process.h
│   ├── queue.h
│   ├── scheduler_fcfs.h
│   ├── scheduler_rr.h
│   ├── scheduler_sjf.h
│   └── simulation.h
│
├── src/
│   ├── process.c
│   ├── queue.c
│   ├── scheduler_fcfs.c
│   ├── scheduler_rr.c
│   ├── scheduler_sjf.c
│   └── simulation.c
│
├── tests/
│   ├── test_fcfs.c
│   ├── test_rr.c
│   ├── test_sjf.c
│   └── Makefile
│
└── main.c
```

---

## 🧪 Testes Implementados

Foram implementados testes automáticos baseados no enunciado.

### ✔️ Teste FCFS

Entrada simulada:
- P1: chegada 0, duração 5  
- P2: chegada 2, duração 3  
- P3: chegada 4, duração 1  

Saída esperada:
```
Ordem de execução:
P1 → P2 → P3

Tempo de espera médio: 2.0
Tempo de retorno médio: 6.0
```

---

### ✔️ Teste Round Robin (Quantum = 2)

Entrada:
- P1: chegada 0, duração 5  
- P2: chegada 1, duração 4  
- P3: chegada 2, duração 2  

Saída esperada:
```
Ordem de execução por fatias:
P1 → P2 → P3 → P1 → P2 → P1

Tempo de retorno médio: 7.0
Tempo de espera médio: 3.0
```

---

### ✔️ Teste SJF Preemptivo

Entrada:
- P1: chegada 0, duração 8  
- P2: chegada 1, duração 4  
- P3: chegada 2, duração 2  

Linha do tempo esperada:
```
t=0  → P1
t=1  → P2 preempta P1
t=2  → P3 preempta P2
t=4  → P2 volta
t=8  → P1 volta
```

Saídas:
```
Ordem final: P3 → P2 → P1
Tempo de espera médio: 3.6
Tempo de retorno médio: 10.6
```

---

## ▶️ Como Compilar

### Linux / MacOS
```
make
```

### Windows (MinGW)
```
mingw32-make
```

Será gerado o executável:

```
./simulador
```

---

## ▶️ Como Executar

O programa lê um arquivo `.txt` contendo lista de processos no formato:

```
ID tempo_chegada duracao
P1 0 5
P2 2 3
P3 4 1
```

Executando:

```
./simulador processos.txt FCFS
./simulador processos.txt RR 2
./simulador processos.txt SJF
```

---

## 📊 Exemplo Real de Execução do Programa

Usando FCFS:

```
Processo P1 executando...
Processo P1 finalizado no tempo 5

Processo P2 executando...
Processo P2 finalizado no tempo 8

Processo P3 executando...
Processo P3 finalizado no tempo 9

Tempo de espera médio: 2.0
Tempo de retorno médio: 6.0
```


