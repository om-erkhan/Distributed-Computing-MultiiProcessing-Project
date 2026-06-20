"""
dijkstra_parallel.py
====================
Parallel Dijkstra using Python multiprocessing.

Strategy
--------
The graph is partitioned into P chunks (one per worker process).
Each worker relaxes the edges of its chunk independently, then the
main process merges results and iterates until convergence.

This mirrors what OpenMP does in C: the relaxation loop is the
embarrassingly-parallel section.

Why multiprocessing and not threading?
--------------------------------------
Python's GIL (Global Interpreter Lock) prevents true parallelism
with threads for CPU-bound work. multiprocessing spawns real OS
processes so all CPU cores are used — equivalent to OpenMP threads.
"""

import heapq
import time
import multiprocessing as mp
from functools import partial


# ── Worker function (runs in a separate process) ─────────────────────────────

def _relax_chunk(args):
    """
    Relax edges for a subset of nodes.
    Receives a list of (node, [(neighbor, weight)]) pairs,
    plus the current distances dict.
    Returns a list of (neighbor, new_cost, via_node) proposals.
    """
    chunk, dist_snapshot = args
    proposals = []
    for u, neighbors in chunk:
        current = dist_snapshot.get(u, float("inf"))
        if current == float("inf"):
            continue
        for neighbor, weight in neighbors:
            new_cost = current + weight
            if new_cost < dist_snapshot.get(neighbor, float("inf")):
                proposals.append((neighbor, new_cost, u))
    return proposals


# ── Public API ───────────────────────────────────────────────────────────────

def dijkstra_parallel(graph, source, destination, num_workers=None):
    """
    Parameters
    ----------
    graph       : dict  { node_id: [(neighbor, weight), ...] }
    source      : int   starting node
    destination : int   target node
    num_workers : int   number of parallel processes (default: CPU count)

    Returns
    -------
    (distance, path, elapsed_ms)
    """
    if num_workers is None:
        num_workers = mp.cpu_count()

    start_time = time.perf_counter()

    INF   = float("inf")
    nodes = list(graph.keys())

    dist = {n: INF  for n in nodes}
    prev = {n: None for n in nodes}
    dist[source] = 0.0

    visited = set()

    # Split nodes into chunks for parallel processing
    chunk_size = max(1, len(nodes) // num_workers)
    node_items = list(graph.items())   # [(node, [neighbors]), ...]
    chunks     = [node_items[i: i + chunk_size]
                  for i in range(0, len(node_items), chunk_size)]

    # Use a pool – reuse processes across iterations
    with mp.Pool(processes=num_workers) as pool:

        # Dijkstra iterations (each round settles at least one node)
        for _ in range(len(nodes)):

            # ── Find unvisited node with minimum distance ─────────────────
            # (This step stays sequential – it's O(nodes) not the bottleneck)
            u = None
            min_d = INF
            for n in nodes:
                if n not in visited and dist[n] < min_d:
                    min_d = dist[n]
                    u = n

            if u is None or u == destination:
                break

            visited.add(u)

            # ── Parallel edge relaxation ──────────────────────────────────
            dist_snapshot = dict(dist)          # pass a snapshot to workers
            args = [(chunk, dist_snapshot) for chunk in chunks]
            results = pool.map(_relax_chunk, args)

            # ── Merge proposals back in the main process ──────────────────
            for proposals in results:
                for neighbor, new_cost, via in proposals:
                    if new_cost < dist[neighbor]:
                        dist[neighbor] = new_cost
                        prev[neighbor] = via

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # ── Reconstruct path ──────────────────────────────────────────────────
    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    if not path or path[0] != source:
        path = []

    return dist[destination], path, elapsed_ms
