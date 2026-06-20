"""
main.py
=======
Interactive menu for the Parallel Dijkstra project.

Usage
-----
  python generate_db.py     # run once to create the database
  python main.py            # then run this anytime
"""

import os
import sys
import multiprocessing

import db_loader
from dijkstra_sequential import dijkstra          as seq_dijkstra
from dijkstra_parallel   import dijkstra_parallel as par_dijkstra


# ── Helpers ───────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header():
    print("\n" + "═" * 62)
    print("   Parallel Dijkstra Shortest Path  │  Python + SQLite")
    print("═" * 62)


def check_db():
    if not os.path.exists("graph.db"):
        print("\n  ⚠  graph.db not found!")
        print("  Run this first:  python generate_db.py\n")
        sys.exit(1)


def ask_node(prompt, node_ids):
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) in node_ids:
            return int(raw)
        # Try by label substring
        conn = db_loader.get_connection()
        row  = conn.execute(
            "SELECT node_id FROM nodes WHERE label LIKE ? LIMIT 1",
            (f"%{raw}%",)
        ).fetchone()
        conn.close()
        if row:
            return row["node_id"]
        print(f"  Node '{raw}' not found. Enter a valid node_id (1–{max(node_ids)}).")


def display_path(path, node_info, cost, algo_name, elapsed_ms):
    print(f"\n  ── Result ({algo_name}) ──────────────────────────────")
    if not path:
        print("  No path found between those nodes.")
        return

    print(f"  Nodes in path : {len(path)}")
    print(f"  Total cost    : {cost:.4f}")
    print(f"  Time taken    : {elapsed_ms:.3f} ms\n")

    print("  Path:")
    for i, nid in enumerate(path):
        info   = node_info.get(nid, {})
        label  = info.get("label", str(nid))
        city   = info.get("city",  "?")
        arrow  = "  →  " if i < len(path) - 1 else ""
        print(f"    [{nid:4d}] {label:<30} ({city}){arrow}")

    print()


# ── Menu options ──────────────────────────────────────────────────────────────

def menu_find_path(graph, node_info, node_ids):
    header()
    print("  FIND SHORTEST PATH\n")

    print(f"  Available node IDs: 1 – {max(node_ids)}  (total {len(node_ids):,} nodes)\n")

    src = ask_node("  Enter SOURCE node ID : ", set(node_ids))
    dst = ask_node("  Enter DEST   node ID : ", set(node_ids))

    if src == dst:
        print("  Source and destination are the same node.")
        input("\n  Press Enter to continue …")
        return

    print(f"\n  Running Sequential Dijkstra …")
    cost_s, path_s, ms_s = seq_dijkstra(graph, src, dst, len(node_ids))
    display_path(path_s, node_info, cost_s, "Sequential", ms_s)

    workers = multiprocessing.cpu_count()
    print(f"  Running Parallel Dijkstra ({workers} cores) …")
    cost_p, path_p, ms_p = par_dijkstra(graph, src, dst, num_workers=workers)
    display_path(path_p, node_info, cost_p, f"Parallel ({workers} cores)", ms_p)

    # Speedup summary
    if ms_s > 0 and ms_p > 0:
        speedup = ms_s / ms_p
        print(f"  Speedup: {speedup:.2f}x  (parallel was "
              f"{'faster' if speedup > 1 else 'slower'} than sequential)")

    # Save to DB
    db_loader.save_result(src, dst, cost_s, path_s, "Sequential",  ms_s)
    db_loader.save_result(src, dst, cost_p, path_p, f"Parallel-{workers}", ms_p)
    print("\n  Results saved to database ✓")

    input("\n  Press Enter to continue …")


def menu_stats(node_ids):
    header()
    print("  DATABASE STATISTICS\n")
    print(f"  Total nodes  : {db_loader.get_node_count():,}")
    print(f"  Total edges  : {db_loader.get_edge_count():,}")
    print(f"  Node ID range: 1 – {max(node_ids)}")
    print(f"  CPU cores    : {multiprocessing.cpu_count()}")

    print("\n  Recent computations:")
    results = db_loader.get_recent_results(5)
    if not results:
        print("  (none yet)")
    else:
        print(f"  {'#':<4} {'From':>6} {'To':>6} {'Cost':>10} {'Algorithm':<18} {'Time (ms)':>10}")
        print("  " + "─" * 58)
        for i, r in enumerate(results, 1):
            print(f"  {i:<4} {r['source_node']:>6} {r['dest_node']:>6} "
                  f"{r['total_cost']:>10.2f} {r['algorithm']:<18} {r['exec_time_ms']:>10.3f}")

    input("\n  Press Enter to continue …")


def menu_benchmark():
    header()
    print("  PERFORMANCE BENCHMARK\n")
    print("  This will run both algorithms on several random pairs")
    print("  and display a full speedup / efficiency report.\n")
    confirm = input("  Start benchmark? (y/n): ").strip().lower()
    if confirm == "y":
        from benchmark import run_benchmark
        run_benchmark()
    input("\n  Press Enter to continue …")


def menu_sample_nodes(node_ids):
    header()
    print("  SAMPLE NODE LIST  (first 20)\n")
    conn = db_loader.get_connection()
    rows = conn.execute(
        "SELECT node_id, label, city, x_coord, y_coord FROM nodes LIMIT 20"
    ).fetchall()
    conn.close()
    print(f"  {'ID':>5}  {'Label':<35} {'City':<15} {'X':>8} {'Y':>8}")
    print("  " + "─" * 74)
    for r in rows:
        print(f"  {r['node_id']:>5}  {r['label']:<35} {r['city']:<15} "
              f"{r['x_coord']:>8.2f} {r['y_coord']:>8.2f}")
    input("\n  Press Enter to continue …")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    check_db()

    print("\nLoading graph …", end=" ", flush=True)
    graph, node_info = db_loader.load_graph()
    node_ids         = db_loader.get_all_node_ids()
    print(f"done  ({len(node_ids):,} nodes, {db_loader.get_edge_count():,} edges)\n")

    while True:
        clear()
        header()
        print("\n  1.  Find shortest path  (sequential + parallel)")
        print("  2.  View database statistics")
        print("  3.  Run performance benchmark")
        print("  4.  Browse sample nodes")
        print("  5.  Launch Web GUI Dashboard (Interactive Map)")
        print("  0.  Exit\n")

        choice = input("  Choose an option: ").strip()

        if   choice == "1": menu_find_path(graph, node_info, node_ids)
        elif choice == "2": menu_stats(node_ids)
        elif choice == "3": menu_benchmark()
        elif choice == "4": menu_sample_nodes(node_ids)
        elif choice == "5":
            import web_server
            web_server.start_server()
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    # Required on macOS/Windows for multiprocessing
    mp = __import__("multiprocessing")
    mp.freeze_support()
    main()
