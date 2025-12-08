# main.py
from master import Master
from helpers import load_input

def main():
    # CONFIGURAÇÕES PADRÃO (modifique como quiser)
    INPUT_FILE = "example_input.json"     # <-- coloque aqui o nome do arquivo JSON padrão
    POLICY = "RR"                 # opções: RR, SJF, PRIORITY
    ARRIVAL_MEAN = 0              # 0 = chegada imediata
    SEED = 42

    # Carregar JSON
    data = load_input(INPUT_FILE)
    servers = data["servidores"]
    tasks = data["requisicoes"]

    print("Iniciando simulação BSB Compute...")
    print(f"Arquivo de entrada: {INPUT_FILE}")
    print(f"Política: {POLICY}")
    print(f"Arrival mean: {ARRIVAL_MEAN}")

    # Criar Master
    m = Master(
        servers,
        tasks,
        policy=POLICY,
        arrival_mean=(ARRIVAL_MEAN if ARRIVAL_MEAN > 0 else 0.01),
        seed=SEED,
        realtime=(ARRIVAL_MEAN > 0)
    )

    # Rodar simulação
    m.run()
    m.print_summary()


if __name__ == "__main__":
    main()
