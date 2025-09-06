"""
algorithms.py
-------------
Basic graph algorithms for shortest path on the travel app.
Uses adjacency built from data_loader.py
"""

import heapq
from data_loader import get_edge_weight

def dijkstra(adj, start, end, factor="distance"):
    pq = [(0, start, [])]
    visited = set()
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        path = path + [node]
        if node == end:
            return cost, path
        visited.add(node)
        for neigh, w, edge in adj.get(node, []):
            heapq.heappush(pq, (cost + get_edge_weight(edge, factor), neigh, path))
    return float("inf"), []

def astar(adj, start, end, nodes, factor="distance", heuristic_fn=None):
    if heuristic_fn is None:
        from data_loader import heuristic
        heuristic_fn = lambda a, b: heuristic(a, b, nodes)

    pq = [(0 + heuristic_fn(start, end), 0, start, [])]
    visited = set()
    while pq:
        est, cost, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        path = path + [node]
        if node == end:
            return cost, path
        visited.add(node)
        for neigh, w, edge in adj.get(node, []):
            g = cost + get_edge_weight(edge, factor)
            f = g + heuristic_fn(neigh, end)
            heapq.heappush(pq, (f, g, neigh, path))
    return float("inf"), []
