"""
gen_edges.py
------------
Generate edges.csv from nodes.csv.
Supports:
  --full : full graph
  --knn K : k-nearest neighbors
Includes multiple transport modes: car, bus, train, flight, walk
"""

import csv
import argparse
from data_loader import load_nodes, heuristic

TRANSPORT_MODES = {
    "car":    {"speed_kmh": 80,  "cost_per_km": 0.10, "emission_per_km": 0.12, "safety": 0.7},
    "bus":    {"speed_kmh": 60,  "cost_per_km": 0.05, "emission_per_km": 0.08, "safety": 0.75},
    "train":  {"speed_kmh": 120, "cost_per_km": 0.08, "emission_per_km": 0.04, "safety": 0.85},
    "flight": {"speed_kmh": 700, "cost_per_km": 0.20, "emission_per_km": 0.25, "safety": 0.9},
    "walk":   {"speed_kmh": 5,   "cost_per_km": 0.0,  "emission_per_km": 0.0,  "safety": 0.6},
}

def make_edge(a, b, dist, mode):
    params = TRANSPORT_MODES[mode]
    return {
        "source": a,
        "target": b,
        "mode": mode,
        "distance_km": round(dist, 2),
        "time_min": round((dist / params["speed_kmh"]) * 60, 1),
        "cost_usd": round(dist * params["cost_per_km"], 2),
        "emission_kgco2": round(dist * params["emission_per_km"], 2),
        "safety_score": params["safety"],
        "accessible": True,
    }

def build_full_graph(nodes, modes):
    edges = []
    node_list = list(nodes.keys())
    for i in range(len(node_list)):
        for j in range(i + 1, len(node_list)):
            a, b = node_list[i], node_list[j]
            dist = heuristic(a, b, nodes)
            for m in modes:
                edges.append(make_edge(a, b, dist, m))
    return edges

def build_k_nearest_graph(nodes, k, modes):
    edges = []
    for a in nodes.keys():
        neighbors = [(b, heuristic(a, b, nodes)) for b in nodes if b != a]
        neighbors.sort(key=lambda x: x[1])
        for b, dist in neighbors[:k]:
            for m in modes:
                edges.append(make_edge(a, b, dist, m))
    return edges

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate edges.csv from nodes.csv")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true", help="Generate full graph")
    group.add_argument("--knn", type=int, help="Generate k-nearest neighbor graph")
    parser.add_argument("--nodes", default="../data/nodes.csv", help="Path to nodes.csv")
    parser.add_argument("--out", default="../data/edges.csv", help="Path to output edges.csv")
    parser.add_argument("--modes", nargs="+", default=["car", "train", "flight"],
                        help="Transport modes to include (default: car train flight)")

    args = parser.parse_args()
    nodes = load_nodes(args.nodes)

    if args.full:
        edges = build_full_graph(nodes, args.modes)
    else:
        edges = build_k_nearest_graph(nodes, args.knn, args.modes)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
        writer.writeheader()
        writer.writerows(edges)

    print(f"Saved {len(edges)} edges to {args.out}")
