import json
from http.server import BaseHTTPRequestHandler

hostName = "localhost"
hostPort = 5000


class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        # self.send_header("Content-type", "text/html")
        # self.end_headers()

    def do_POST(self):
        length = int(self.headers['Content-Length'])

        response = json.loads(self.rfile.read(length).decode('utf-8'))

        with open('./slimano/input/callback_payload', 'w+') as f:
            f.write(json.dumps(response))

        self.send_response(200)
        self.end_headers()

        import threading
        assassin = threading.Thread(target=self.server.shutdown)
        assassin.daemon = True
        assassin.start()

