"""
generate_db.py
==============
Creates the SQLite database with 5,000+ records (nodes + edges).
Run this FIRST before anything else.
"""

import sqlite3
import random
import math
import os

DB_PATH = "graph.db"
NUM_NODES = 500
NUM_EDGES = 5000   # satisfies the 5,000 record requirement


def euclidean_weight(x1, y1, x2, y2):
    return round(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2), 2)


def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Schema ──────────────────────────────────────────────────────────────
    c.executescript("""
        CREATE TABLE nodes (
            node_id   INTEGER PRIMARY KEY,
            label     TEXT    NOT NULL,
            x_coord   REAL    NOT NULL,
            y_coord   REAL    NOT NULL,
            city      TEXT    NOT NULL
        );

        CREATE TABLE edges (
            edge_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node INTEGER NOT NULL,
            dest_node   INTEGER NOT NULL,
            weight      REAL    NOT NULL,
            road_type   TEXT    NOT NULL,
            FOREIGN KEY (source_node) REFERENCES nodes(node_id),
            FOREIGN KEY (dest_node)   REFERENCES nodes(node_id)
        );

        CREATE TABLE shortest_path_results (
            result_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node  INTEGER NOT NULL,
            dest_node    INTEGER NOT NULL,
            total_cost   REAL,
            path_string  TEXT,
            algorithm    TEXT,
            exec_time_ms REAL,
            computed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_edges_source ON edges(source_node);
        CREATE INDEX idx_edges_dest   ON edges(dest_node);
    """)

    # ── Nodes ────────────────────────────────────────────────────────────────
    cities = [
        "Manila", "Cebu", "Davao", "Quezon City", "Makati",
        "Pasig",  "Taguig", "Mandaluyong", "Paranaque", "Caloocan"
    ]

    random.seed(42)
    nodes = []
    for i in range(1, NUM_NODES + 1):
        city  = random.choice(cities)
        label = f"Node_{i:04d}_{city[:3].upper()}"
        x     = round(random.uniform(0, 1000), 4)
        y     = round(random.uniform(0, 1000), 4)
        nodes.append((i, label, x, y, city))

    c.executemany(
        "INSERT INTO nodes (node_id, label, x_coord, y_coord, city) VALUES (?,?,?,?,?)",
        nodes
    )
    print(f"  ✓  Inserted {len(nodes)} nodes")

    # ── Edges ────────────────────────────────────────────────────────────────
    road_types  = ["Highway", "National Road", "City Road", "Local Street", "Expressway"]
    node_coords = {n[0]: (n[2], n[3]) for n in nodes}

    edge_set = set()
    edges    = []

    # 1) Guarantee connectivity: chain all nodes so there is always a path
    shuffled = list(range(1, NUM_NODES + 1))
    random.shuffle(shuffled)
    for i in range(len(shuffled) - 1):
        a, b = shuffled[i], shuffled[i + 1]
        x1, y1 = node_coords[a]
        x2, y2 = node_coords[b]
        w = euclidean_weight(x1, y1, x2, y2)
        road = random.choice(road_types)
        edges.append((a, b, w, road))
        edges.append((b, a, w, road))
        edge_set.add((a, b))
        edge_set.add((b, a))

    # 2) Fill up to NUM_EDGES with random edges
    attempts = 0
    while len(edges) < NUM_EDGES and attempts < NUM_EDGES * 10:
        a = random.randint(1, NUM_NODES)
        b = random.randint(1, NUM_NODES)
        attempts += 1
        if a == b or (a, b) in edge_set:
            continue
        x1, y1 = node_coords[a]
        x2, y2 = node_coords[b]
        w = round(euclidean_weight(x1, y1, x2, y2) * random.uniform(0.8, 1.5), 2)
        road = random.choice(road_types)
        edges.append((a, b, w, road))
        edge_set.add((a, b))

    c.executemany(
        "INSERT INTO edges (source_node, dest_node, weight, road_type) VALUES (?,?,?,?)",
        edges
    )
    print(f"  ✓  Inserted {len(edges)} edges  (≥ 5,000 requirement met)")

    conn.commit()
    conn.close()
    size_kb = os.path.getsize(DB_PATH) // 1024
    print(f"  ✓  Database saved → {DB_PATH}  ({size_kb} KB)")


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════╗")
    print("║      Generating Graph Database       ║")
    print("╚══════════════════════════════════════╝\n")
    create_database()
    print("\nDone! Run  main.py  next.\n")
