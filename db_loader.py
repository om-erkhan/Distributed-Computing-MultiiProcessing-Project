"""
db_loader.py
============
All SQLite read/write operations for the project.
"""

import sqlite3

DB_PATH = "graph.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Graph loading ─────────────────────────────────────────────────────────────

def load_graph():
    """
    Returns
    -------
    graph      : dict { node_id: [(neighbor_id, weight), ...] }
    node_info  : dict { node_id: {'label': ..., 'city': ..., 'x': ..., 'y': ...} }
    """
    conn = get_connection()
    c    = conn.cursor()

    c.execute("SELECT node_id, label, x_coord, y_coord, city FROM nodes")
    rows = c.fetchall()

    graph     = {r["node_id"]: [] for r in rows}
    node_info = {
        r["node_id"]: {
            "label": r["label"],
            "city":  r["city"],
            "x":     r["x_coord"],
            "y":     r["y_coord"],
        }
        for r in rows
    }

    c.execute("SELECT source_node, dest_node, weight FROM edges")
    for edge in c.fetchall():
        src, dst, w = edge["source_node"], edge["dest_node"], edge["weight"]
        graph[src].append((dst, w))

    conn.close()
    return graph, node_info


def get_node_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    conn.close()
    return count


def get_edge_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    conn.close()
    return count


def get_all_node_ids():
    conn = get_connection()
    rows = conn.execute("SELECT node_id FROM nodes ORDER BY node_id").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_node_label(node_id):
    conn = get_connection()
    row  = conn.execute(
        "SELECT label, city FROM nodes WHERE node_id = ?", (node_id,)
    ).fetchone()
    conn.close()
    if row:
        return f"{row['label']} ({row['city']})"
    return str(node_id)


# ── Result saving ─────────────────────────────────────────────────────────────

def save_result(source, destination, cost, path, algorithm, exec_time_ms):
    path_str = " → ".join(str(n) for n in path) if path else "No path"
    conn = get_connection()
    conn.execute(
        """INSERT INTO shortest_path_results
           (source_node, dest_node, total_cost, path_string, algorithm, exec_time_ms)
           VALUES (?,?,?,?,?,?)""",
        (source, destination, cost, path_str, algorithm, round(exec_time_ms, 4)),
    )
    conn.commit()
    conn.close()


def get_recent_results(limit=10):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM shortest_path_results
           ORDER BY computed_at DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return rows
