# main.py
import argparse
from master import Master
from helpers import load_input

def main():
    parser = argparse.ArgumentParser(description="Simulador BSB Compute (workers paralelos)")
    parser.add_argument("--input", required=True, help="arquivo JSON de entrada (ex: example_input.json)")
    parser.add_argument("--policy", choices=["RR","SJF","PRIORITY"], default="RR")
    parser.add_argument("--arrival-mean", type=float, default=1.0, help="média do tempo entre chegadas (s). 0 -> chegada imediata")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data = load_input(args.input)
    servers = data["servidores"]
    tasks = data["requisicoes"]

    m = Master(servers, tasks, policy=args.policy, arrival_mean=(args.arrival_mean if args.arrival_mean>0 else 0.01), seed=args.seed, realtime=(args.arrival_mean>0))
    m.run()
    m.print_summary()

if __name__ == "__main__":
    main()
