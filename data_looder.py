"""
data_loader.py
--------------
Utility module to load city nodes and route edges for the hackathon travel app.

Provides:
 - load_nodes(path)
 - load_edges(path)
 - build_adjacency(edges, directed=False)
 - get_edge_weight(edge, factor)
 - neighbor_generator(adj, node, factor)
 - normalize_edges(edges, metrics)
 - heuristic(city_a, city_b, nodes)  # straight-line (haversine) distance
 - quick_tests(nodes, edges, adj)
 - demo()  # small demo that runs when executed as script
"""

import csv
import math
from collections import defaultdict, deque

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def load_nodes(path="data/nodes.csv"):
    """Load nodes.csv and return dict: {city: {country, lat, lon, ...}}"""
    nodes = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            city = r.get("city") or r.get("name")
            if not city:
                continue
            nodes[city] = {
                "country": r.get("country"),
                "lat": float(r.get("lat")) if r.get("lat") else None,
                "lon": float(r.get("lon")) if r.get("lon") else None,
                "raw": r
            }
    return nodes

def load_edges(path="data/edges.csv"):
    """Load edges.csv and return list of edge dicts."""
    edges = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                edge = {
                    "source": r["source"],
                    "target": r["target"],
                    "mode": r.get("mode", "unknown"),
                    "distance_km": float(r.get("distance_km") or 0.0),
                    "time_min": float(r.get("time_min") or 0.0),
                    "cost_usd": float(r.get("cost_usd") or 0.0),
                    "emission_kgco2": float(r.get("emission_kgco2") or 0.0),
                    "safety_score": float(r.get("safety_score") or 0.5),
                    "accessible": (str(r.get("accessible", "True")).lower() in ("true","1","yes"))
                }
            except Exception as e:
                print("Skipping bad edge row:", r, "err:", e)
                continue
            edges.append(edge)
    return edges

def build_adjacency(edges, directed=False):
    """Build adjacency dict: {city: [(neighbor, edge_dict), ...], ...}"""
    adj = defaultdict(list)
    for e in edges:
        s, t = e["source"], e["target"]
        adj[s].append((t, e))
        if not directed:
            mirror = dict(e)
            mirror["source"], mirror["target"] = t, s
            adj[t].append((s, mirror))
    return dict(adj)

def get_edge_weight(edge, factor="distance"):
    if factor == "distance":
        return edge.get("distance_km", float("inf"))
    if factor == "time":
        return edge.get("time_min", float("inf"))
    if factor == "cost":
        return edge.get("cost_usd", float("inf"))
    if factor == "eco":
        return edge.get("emission_kgco2", float("inf"))
    if factor == "safety":
        return 1.0 - edge.get("safety_score", 0.5)
    return edge.get("distance_km", float("inf"))

def neighbor_generator(adj, node, factor="distance"):
    for neigh, edge in adj.get(node, []):
        w = get_edge_weight(edge, factor)
        yield neigh, w, edge

def normalize_edges(edges, metrics=None):
    if metrics is None:
        metrics = ["distance_km", "time_min", "cost_usd", "emission_kgco2"]
    mins, maxs = {}, {}
    for m in metrics:
        values = [e[m] for e in edges if e.get(m) is not None]
        if not values:
            mins[m], maxs[m] = 0.0, 1.0
        else:
            mins[m], maxs[m] = min(values), max(values)
    for e in edges:
        for m in metrics:
            mn, mx = mins[m], maxs[m]
            if mx == mn:
                e[f"norm_{m}"] = 0.0
            else:
                e[f"norm_{m}"] = (e.get(m, mn) - mn) / (mx - mn)
    return edges

def heuristic(city_a, city_b, nodes):
    a = nodes.get(city_a)
    b = nodes.get(city_b)
    if not a or not b or a.get("lat") is None or b.get("lat") is None:
        return 0.0
    return haversine(a["lat"], a["lon"], b["lat"], b["lon"])

def quick_tests(nodes, edges, adj):
    errors = []
    node_names = set(nodes.keys())
    for e in edges:
        if e["source"] not in node_names:
            errors.append(f"Missing source node: {e['source']}")
        if e["target"] not in node_names:
            errors.append(f"Missing target node: {e['target']}")
        if e["distance_km"] < 0: errors.append(f"Negative distance: {e}")
        if e["time_min"] < 0: errors.append(f"Negative time: {e}")
        if e["cost_usd"] < 0: errors.append(f"Negative cost: {e}")
    if nodes:
        from collections import deque
        start = next(iter(node_names))
        visited = {start}
        q = deque([start])
        while q:
            u = q.popleft()
            for v, _ in adj.get(u, []):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        if len(visited) < max(1, len(node_names)//2):
            errors.append("Graph appears sparsely connected")
    return errors

def demo(nodes_path="../data/nodes.csv", edges_path="../data/edges.csv"):
    print("Loading nodes from:", nodes_path)
    nodes = load_nodes(nodes_path)
    print("Loaded nodes:", len(nodes))
    print("Loading edges from:", edges_path)
    edges = load_edges(edges_path)
    print("Loaded edges:", len(edges))
    adj = build_adjacency(edges)
    print("Neighbors for 'Paris':")
    for neigh, w, e in neighbor_generator(adj, "Paris", factor="distance"):
        print(f" - {neigh} via {e['mode']}: {w} km")
    errs = quick_tests(nodes, edges, adj)
    if errs:
        print("Issues found:")
        for er in errs[:10]:
            print(" *", er)
    else:
        print("Graph looks OK")
    return nodes, edges, adj

if __name__ == '__main__':
    demo()
