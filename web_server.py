#!/usr/bin/env python3
"""
web_server.py
=============
Lightweight, zero-dependency REST API server using Python's built-in http.server.
Serves the GUI web application and executes sequential/parallel Dijkstra routing.
"""

import http.server
import socketserver
import json
import urllib.parse
import webbrowser
import os
import multiprocessing

import db_loader
from dijkstra_sequential import dijkstra          as seq_dijkstra
from dijkstra_parallel   import dijkstra_parallel as par_dijkstra

PORT = 8080
GUI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")


class DashboardAPIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default terminal logs for a cleaner console layout
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(GUI_DIR, "index.html"), "text/html")
        elif path == "/api/nodes":
            self.get_nodes()
        elif path == "/api/solve":
            self.solve_path(parsed_url.query)
        elif path == "/api/history":
            self.get_history()
        else:
            self.send_error(404, "File Not Found")

    def serve_file(self, filepath, content_type):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def get_nodes(self):
        try:
            _, node_info = db_loader.load_graph()
            self.send_json(node_info)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def solve_path(self, query_str):
        try:
            params = urllib.parse.parse_qs(query_str)
            src = int(params.get("src", [None])[0])
            dst = int(params.get("dst", [None])[0])

            if src is None or dst is None:
                self.send_json({"status": "error", "message": "Missing src or dst parameters"}, status_code=400)
                return

            graph, _ = db_loader.load_graph()
            node_ids = db_loader.get_all_node_ids()

            # Execute sequential
            cost_s, path_s, ms_s = seq_dijkstra(graph, src, dst, len(node_ids))
            
            # Execute parallel
            workers = multiprocessing.cpu_count()
            cost_p, path_p, ms_p = par_dijkstra(graph, src, dst, num_workers=workers)

            # Log audits in SQLite
            db_loader.save_result(src, dst, cost_s, path_s, "Sequential", ms_s)
            db_loader.save_result(src, dst, cost_p, path_p, f"Parallel-{workers}", ms_p)

            # Return stats
            response = {
                "status": "success",
                "path": path_s,
                "cost": cost_s,
                "seq_time_ms": ms_s,
                "par_time_ms": ms_p
            }
            self.send_json(response)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def get_history(self):
        try:
            rows = db_loader.get_recent_results(10)
            history = []
            for r in rows:
                history.append({
                    "result_id": r["result_id"],
                    "source_node": r["source_node"],
                    "dest_node": r["dest_node"],
                    "total_cost": r["total_cost"],
                    "algorithm": r["algorithm"],
                    "exec_time_ms": r["exec_time_ms"],
                    "computed_at": r["computed_at"]
                })
            self.send_json(history)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def start_server():
    # Force use of DualStackServer if available, fallback to TCPServer
    handler = DashboardAPIHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("\n" + "═" * 62)
        print(f"      LAUNCHING INTERACTIVE WEB DASHBOARD PORT {PORT}")
        print("═" * 62)
        print(f"  --> Local address: http://localhost:{PORT}")
        print("  --> Starting web browser automatically...")
        print("  --> Press Ctrl+C in this terminal to shut down server.")
        print("═" * 62 + "\n")
        
        # Open default web browser tab
        webbrowser.open(f"http://localhost:{PORT}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server. Returning to menu...")
            httpd.server_close()


if __name__ == "__main__":
    start_server()
