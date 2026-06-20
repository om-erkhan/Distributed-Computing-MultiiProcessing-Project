"""
dijkstra_sequential.py
======================
Classic single-threaded Dijkstra using a min-heap (priority queue).
Returns the shortest path and total cost between two nodes.
"""

import heapq
import time


def dijkstra(graph, source, destination, num_nodes):
    """
    Parameters
    ----------
    graph       : dict  { node_id: [(neighbor, weight), ...] }
    source      : int   starting node ID
    destination : int   target  node ID
    num_nodes   : int   total number of nodes (for reference)

    Returns
    -------
    (distance, path, elapsed_ms)
        distance   – total shortest-path cost  (float, or inf if unreachable)
        path       – list of node IDs from source to destination
        elapsed_ms – wall-clock time in milliseconds
    """

    start_time = time.perf_counter()

    # ── Initialise ───────────────────────────────────────────────────────────
    INF  = float("inf")
    dist = {node: INF for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0.0

    # min-heap: (cost, node)
    heap = [(0.0, source)]

    visited = set()

    # ── Main loop ────────────────────────────────────────────────────────────
    while heap:
        current_cost, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        if u == destination:          # early exit once target is settled
            break

        for neighbor, weight in graph.get(u, []):
            if neighbor in visited:
                continue
            new_cost = current_cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = u
                heapq.heappush(heap, (new_cost, neighbor))

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # ── Reconstruct path ─────────────────────────────────────────────────────
    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    # If path doesn't start at source, destination is unreachable
    if path[0] != source:
        path = []

    return dist[destination], path, elapsed_ms
