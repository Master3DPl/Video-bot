import http.server
import socketserver
import threading
import os

# Render требует, чтобы приложение открывало порт из переменной окружения PORT
PORT = int(os.environ.get("PORT", 10000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving healthcheck on port {PORT}")
        httpd.serve_forever()

def start_healthcheck_server():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
