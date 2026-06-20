# Parallel Dijkstra Shortest Path — Setup & Run Guide

## Quick Start (3 commands)

```bash
cd dijkstra_project
python generate_db.py     # creates graph.db with 5,000+ records
python main.py            # launches the program
```

That's it. No pip installs. No compiler. Runs on any Mac with Python 3.

---

## What each file does

| File | Purpose |
|---|---|
| `generate_db.py` | Creates `graph.db` — run this ONCE first |
| `main.py` | Interactive menu — run this every time after |
| `dijkstra_sequential.py` | The classic single-core algorithm |
| `dijkstra_parallel.py` | The parallel version (uses all CPU cores) |
| `db_loader.py` | Reads/writes the SQLite database |
| `benchmark.py` | Full performance report (called from menu option 3) |
| `REPORT.md` | Complete project documentation / performance analysis |

---

## AI Prompt for Generating Your Writeup / Documentation

Copy this prompt into ChatGPT or Claude to generate a professional
project documentation, introduction, or presentation script:

---

### PROMPT (copy everything below the line)

---

You are a technical writer helping a university student document their
programming project. Write a professional project documentation for the
following system:

**Project Title:**
Parallel Implementation of Dijkstra's Shortest Path Algorithm
Using Python Multiprocessing on a Large SQLite Database

**What the project does:**
- Implements Dijkstra's shortest path algorithm in Python
- Uses a SQLite database containing 500 nodes and 5,000+ edges
  representing a road network graph
- Runs the algorithm in two modes: sequential (single-core) and
  parallel (multi-core using Python's multiprocessing module)
- Measures and compares execution time, speedup, and efficiency
  between both modes
- Provides an interactive menu where users can find shortest paths,
  view database statistics, and run benchmarks

**Why multiprocessing instead of OpenMP:**
Python's Global Interpreter Lock (GIL) prevents true CPU parallelism
with threads. The multiprocessing module spawns real OS-level processes
that each use a separate CPU core — this is the Python equivalent of
OpenMP in C/C++. The edge relaxation step of Dijkstra's algorithm is
parallelized across worker processes.

**Technical details:**
- Language: Python 3 (no external libraries required)
- Database: SQLite (built-in to Python)
- Parallelism: multiprocessing.Pool with map()
- Algorithm: Min-heap Dijkstra with parallel relaxation
- Performance metric: wall-clock time via time.perf_counter()
- Speedup formula: T_sequential / T_parallel
- Efficiency formula: Speedup / NumCores × 100%

**Please write:**
1. An abstract (150 words)
2. An introduction explaining the problem and motivation (300 words)
3. A methodology section describing the parallel approach (200 words)
4. A results/analysis section with a sample performance table
   showing speedup for 1, 2, and 4 cores (200 words)
5. A conclusion (100 words)

Use formal academic language suitable for a university computer science
course. Mention Amdahl's Law in the analysis section.

---

### END OF PROMPT

---

## Troubleshooting

**"No module named sqlite3"**
→ Reinstall Python from https://python.org (official installer includes sqlite3)

**"graph.db not found"**
→ Run `python generate_db.py` first

**Program is slow on benchmark**
→ Normal — Python has process-spawn overhead. Benchmark shows real speedup
  once processes are warmed up. Parallel advantage grows with graph size.

**Mac says "python not found"**
→ Try `python3 generate_db.py` and `python3 main.py` instead
