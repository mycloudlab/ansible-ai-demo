"""Presenter panel and bounded HTTP proxy, independent of the Java JVM."""
import http.client, json, subprocess, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
LOCK = threading.Lock()
ACTIONS = {'database', 'oom'}
def control(action):
    return subprocess.run(['/usr/bin/sudo', '-n', '/usr/bin/python3', '/opt/caixa-demo-panel/control.py', action], capture_output=True, text=True, timeout=25)
class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup(); self.connection.settimeout(12)
    def log_message(self, *args): pass
    def reply(self, code, content, kind='application/json', headers=None):
        data = content.encode() if isinstance(content, str) else content
        self.send_response(code); self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(data))); self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff')
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(data)
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def handle_request(self):
        path = urlsplit(self.path).path
        if path in ('/demo', '/demo/') and self.command == 'GET':
            return self.reply(200, Path('/opt/caixa-demo-panel/index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/demo/status' and self.command == 'GET':
            r = control('status')
            return self.reply(200 if r.returncode == 0 else 503, r.stdout if r.returncode == 0 else '{"error":"Estado indisponível"}')
        if path.startswith('/api/demo/'):
            action = path.removeprefix('/api/demo/')
            # Browsers must originate here; custom header also prevents form-based CSRF.
            expected = 'http://' + self.headers.get('Host', '')
            if self.command != 'POST' or self.headers.get('Origin') != expected or self.headers.get('X-Demo-Control') != 'presenter':
                return self.reply(403, '{"error":"Origem não autorizada"}')
            if action not in ACTIONS: return self.reply(404, '{}')
            if not LOCK.acquire(blocking=False): return self.reply(409, '{"error":"Aguarde a operação atual"}')
            try:
                r = control(action)
                return self.reply(200 if r.returncode == 0 else 409, json.dumps({'message': 'Comando executado. Observe o estado e solicite o diagnóstico à IA.'} if r.returncode == 0 else {'error': 'Restaure o cenário anterior antes de ativar outra falha.'}))
            finally: LOCK.release()
        if path not in ('/', '/health', '/people'): return self.reply(404, '{}')
        try: length = int(self.headers.get('Content-Length', '0'))
        except ValueError: return self.reply(400, '{}')
        if length < 0 or length > 4096 or self.headers.get('Transfer-Encoding'): return self.reply(413, '{}')
        conn = http.client.HTTPConnection('127.0.0.1', 8081, timeout=6)
        try:
            conn.request(self.command, self.path, body=self.rfile.read(length) if length else None, headers={'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded')})
            r = conn.getresponse(); body = r.read(65536)
            headers = {'X-Request-Id': r.getheader('X-Request-Id')} if r.getheader('X-Request-Id') else {}
            self.reply(r.status, body, r.getheader('Content-Type', 'text/plain'), headers)
        except (OSError, http.client.HTTPException):
            self.reply(503, '<h1>Aplicação indisponível</h1><p>A JVM do cadastro não está respondendo.</p><a href="/demo">Voltar ao painel da demonstração</a>', 'text/html; charset=utf-8')
        finally: conn.close()
if __name__ == '__main__': ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
