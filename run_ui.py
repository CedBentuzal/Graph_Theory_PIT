"""
run_ui.py — One-click launcher for the TSP Dynamic Programming Web UI Dashboard.

Usage:
    py run_ui.py
    # or
    python run_ui.py

This automatically launches a local web server and opens the interactive
dashboard in your default web browser.
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

if not UI_DIR.exists():
    print(f"Error: UI directory not found at {UI_DIR}")
    sys.exit(1)

# Change working directory to UI folder for clean serving
os.chdir(UI_DIR)

PORT = 5000
Handler = http.server.SimpleHTTPRequestHandler

# Find an available port if 5000 is occupied
for p in range(5000, 5020):
    try:
        httpd = socketserver.TCPServer(("", p), Handler)
        PORT = p
        break
    except OSError:
        continue

url = f"http://localhost:{PORT}/index.html"
print("=" * 65)
print("  TSP DYNAMIC PROGRAMMING SOLVER — INTERACTIVE WEB DASHBOARD")
print("  Real-World Application: Cagayan de Oro City Water District (COWD)")
print("=" * 65)
print(f"\n  Serving interactive UI from: {UI_DIR}")
print(f"  Access URL: {url}\n")
print("  Opening dashboard in your web browser...")
print("  Press Ctrl+C in this terminal to stop the server.\n")

webbrowser.open(url)

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\n  Server stopped. Exiting cleanly.")
    httpd.server_close()
