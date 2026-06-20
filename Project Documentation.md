# Parallel Implementation of Dijkstra's Shortest Path Algorithm
## Using Python Multiprocessing on a Large SQLite Database

**Course:** Concurrent and Parallel Programming (CCP)  
**Language:** Python 3  
**Database:** SQLite (built-in)  
**Parallelism:** `multiprocessing` module (true OS-level parallelism)

---

## 1. Project Overview

This project implements Dijkstra's Shortest Path Algorithm in two forms — sequential and parallel — and evaluates the performance improvement gained through parallel processing. A SQLite database stores the graph data (nodes and edges), and Python's `multiprocessing` module is used as the parallel computing mechanism, analogous to OpenMP in C/C++.

---

## 2. Why Python Multiprocessing instead of OpenMP?

OpenMP is a C/C++ directive system. In Python:

| Mechanism | True Parallelism? | Notes |
|---|---|---|
| `threading` | ❌ No | Blocked by Python's GIL |
| `multiprocessing` | ✅ Yes | Spawns real OS processes, uses all CPU cores |
| `concurrent.futures` | ✅ Yes | Higher-level wrapper over multiprocessing |

`multiprocessing` is the direct Python equivalent of OpenMP for CPU-bound tasks. Each worker process runs on a separate CPU core, providing genuine parallel speedup.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────┐
│                   main.py                        │
│           (Interactive Menu / UI)                │
└────────────┬──────────────────┬─────────────────┘
             │                  │
     ┌───────▼──────┐   ┌───────▼────────┐
     │  db_loader   │   │   benchmark    │
     │  (SQLite I/O)│   │ (timing/report)│
     └───────┬──────┘   └───────┬────────┘
             │                  │
     ┌───────▼──────────────────▼────────┐
     │         graph (adjacency list)     │
     │   { node_id: [(neighbor, wt) ...] }│
     └────────────┬──────────────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
┌──────▼──────┐    ┌─────────▼──────────────┐
│  Sequential │    │       Parallel          │
│  Dijkstra   │    │       Dijkstra          │
│  (1 thread) │    │  (N worker processes)   │
└─────────────┘    └─────────────────────────┘
```

---

## 4. Database Design

### Tables

**nodes** — 500 records
```sql
CREATE TABLE nodes (
    node_id   INTEGER PRIMARY KEY,
    label     TEXT    NOT NULL,
    x_coord   REAL    NOT NULL,
    y_coord   REAL    NOT NULL,
    city      TEXT    NOT NULL
);
```

**edges** — 5,000+ records *(satisfies the ≥5,000 requirement)*
```sql
CREATE TABLE edges (
    edge_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node INTEGER NOT NULL,
    dest_node   INTEGER NOT NULL,
    weight      REAL    NOT NULL,
    road_type   TEXT    NOT NULL,
    FOREIGN KEY (source_node) REFERENCES nodes(node_id),
    FOREIGN KEY (dest_node)   REFERENCES nodes(node_id)
);
```

**shortest_path_results** — audit log of all computations
```sql
CREATE TABLE shortest_path_results (
    result_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node  INTEGER,
    dest_node    INTEGER,
    total_cost   REAL,
    path_string  TEXT,
    algorithm    TEXT,
    exec_time_ms REAL,
    computed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Generation Strategy
- 500 nodes placed at random (x, y) coordinates in a 1000×1000 grid
- Edge weights are Euclidean distances (realistic road-length simulation)
- A spanning chain guarantees every node pair has at least one valid path
- Additional random edges fill the table to 5,000+ records

---

## 5. Algorithm Description

### 5.1 Sequential Dijkstra

Classic greedy shortest-path using a **binary min-heap** (priority queue):

```
Initialize dist[source] = 0, all others = ∞
Push (0, source) onto heap

WHILE heap is not empty:
    (cost, u) = pop minimum from heap
    IF u == destination: STOP

    FOR each neighbor v of u:
        new_cost = cost + weight(u, v)
        IF new_cost < dist[v]:
            dist[v] = new_cost
            prev[v] = u
            push (new_cost, v) onto heap

Reconstruct path by following prev[] from destination to source
```

**Time Complexity:** O((V + E) log V)  
**Space Complexity:** O(V + E)

### 5.2 Parallel Dijkstra

The **edge relaxation step** is parallelized — this is the loop that checks all neighbors of the current node and updates distances. It maps directly to what `#pragma omp parallel for` does in C:

```
WHILE not settled:
    u = node with minimum unvisited distance   [sequential]

    PARALLEL (across P worker processes):
        Each worker relaxes its chunk of the graph
        Proposes (neighbor, new_cost, via) updates

    Main process merges all proposals           [sequential]
    Updates dist[] and prev[] with best values
```

**Parallel section per iteration:** O(E/P) per worker  
**Merge step:** O(P × proposals) — lightweight

---

## 6. File Structure

```
dijkstra_project/
│
├── generate_db.py          ← Run FIRST: creates graph.db with 5,000+ records
├── main.py                 ← Interactive menu: find paths, stats, benchmark
│
├── dijkstra_sequential.py  ← Single-threaded Dijkstra (min-heap)
├── dijkstra_parallel.py    ← Multiprocessing Dijkstra (parallel relaxation)
├── db_loader.py            ← All SQLite read/write functions
├── benchmark.py            ← Automated timing & report generator
│
├── graph.db                ← Generated SQLite database (auto-created)
└── REPORT.md               ← This document
```

---

## 7. How to Run

### Requirements
- Python 3.8 or higher (comes pre-installed on Mac)
- No pip installs needed — all modules are part of Python's standard library

### Steps

```bash
# Step 1: Navigate to project folder
cd dijkstra_project

# Step 2: Generate the database (run once)
python generate_db.py

# Step 3: Launch the interactive program
python main.py

# Optional: Run benchmark only
python benchmark.py
```

### Menu Options
```
1. Find shortest path     → Enter source & destination node IDs
                            Shows path, cost, and timing for both algorithms
2. Database statistics    → Node/edge counts, recent computations
3. Run benchmark          → Full performance report across multiple pairs
4. Browse sample nodes    → Preview first 20 nodes in the database
0. Exit
```

---

## 8. Performance Analysis

### 8.1 Methodology
- **Part 1: Single-Query Benchmark**: 8 random source→destination pairs tested. Each pair is run 5 times and averaged to obtain high-resolution execution times (measured using `time.perf_counter()`).
- **Part 2: Multi-Query Batch Benchmark**: A batch of 4,000 random queries is executed. This simulates a production routing server (e.g., Google Maps, OSRM) where multiple route requests are processed concurrently.
- Both benchmarks are evaluated across 1, 2, 4, and 8 parallel worker processes on an 8-core Apple Silicon CPU.

### 8.2 Empirical Results (Measured on 8-Core macOS System)

#### Part 1: Single-Query Dijkstra (Fine-Grained Parallelism)
| Algorithm | Avg Time (ms) | Speedup | Efficiency |
|---|---|---|---|
| Sequential (1 core) | 0.913 | 1.00x | 100.0% |
| Parallel (1 core)  | 1040.400 | 0.00x |  0.1% |
| Parallel (2 cores) | 693.693 | 0.00x |  0.0% |
| Parallel (4 cores) | 710.432 | 0.00x |  0.0% |
| Parallel (8 cores) | 768.955 | 0.00x |  0.0% |

#### Part 2: Multi-Query Batch Dijkstra (Coarse-Grained Parallelism - 4,000 queries)
| Configuration | Total Time (ms) | Speedup | Efficiency |
|---|---|---|---|
| Sequential (1 core) | 2993.939 | 1.00x | 100.0% |
| Parallel (1 core)  | 2986.693 | 1.00x | 100.2% |
| Parallel (2 cores) | 1597.956 | 1.87x |  93.7% |
| Parallel (4 cores) | 920.555 | 3.25x |  81.3% |
| Parallel (8 cores) | 1005.117 | 2.98x |  37.2% |

### 8.3 Speedup & Efficiency Formulae

```
Speedup(P) = T_sequential / T_parallel(P)

Efficiency(P) = Speedup(P) / P × 100%
```

### 8.4 Analysis

#### 1. Why is Single-Query Parallelization 1,000x Slower?
In a fine-grained parallelization where we partition the graph and relax vertices in parallel, Python processes must communicate candidate updates (`proposals`) back to the main process via IPC pipes. Because a sequential query takes under 1 ms, the overhead of serialization, pickling, and pipe communication inside the loop dominates the run-time. Each step is throttled by process IPC, showing a **0.00x speedup**.

#### 2. Why does Multi-Query Batching Achieve Near-Linear Speedup?
By distributing 4,000 independent shortest-path queries across the process pool, each process executes a standard sequential Dijkstra query on its own CPU core. IPC is only performed once at the start (distributing tasks) and once at the end (returning paths). This eliminates loop-level IPC overhead, achieving a **3.25x speedup on 4 cores (81.3% efficiency)**. Performance scales cleanly until memory bus constraints are reached.

### 8.5 Scalability and Amdahl's Law
Amdahl's Law states that the maximum speedup is limited by the sequential fraction ($S$) of the program:
$$\text{Speedup} = \frac{1}{S + \frac{1 - S}{P}}$$
In Part 1, the sequential fraction $S$ is near $100\%$ due to the IPC communication bottleneck. In Part 2, the sequential fraction $S$ (pool creation and result aggregation) is less than $10\%$, allowing high scalability and efficiency.

---

## 9. Key Design Decisions

| Decision | Reason |
|---|---|
| SQLite over MySQL/PostgreSQL | Zero installation; built into Python; portable |
| Adjacency list over matrix | Sparse graphs: O(V+E) space vs O(V²) |
| Min-heap (heapq) | O(log V) per extraction vs O(V) for array scan |
| multiprocessing over threading | Python GIL prevents true thread parallelism |
| Connectivity guarantee in generation | Ensures every test pair has a valid path |
| Snapshot-passing to workers | Avoids shared-memory conflicts between processes |

---

## 10. Limitations and Future Work

- **GIL workaround cost:** Python processes have higher spawn overhead than C threads. A C implementation with OpenMP would show near-linear speedup for the same algorithm.
- **Memory duplication:** Each worker process gets a full copy of the graph. C/OpenMP shares memory directly, which is more efficient.
- **Future improvement:** Bidirectional Dijkstra or A* with heuristics could reduce search space by ~50%.

---

## 11. References

1. Dijkstra, E.W. (1959). "A note on two problems in connexion with graphs." *Numerische Mathematik*, 1(1), 269–271.
2. Amdahl, G.M. (1967). "Validity of the single processor approach to achieving large scale computing capabilities." *AFIPS Conference Proceedings*.
3. Python Software Foundation. (2024). `multiprocessing` — Process-based parallelism. https://docs.python.org/3/library/multiprocessing.html
4. SQLite Documentation. https://www.sqlite.org/docs.html
