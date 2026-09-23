"""Serve o front-end do SmartCondo em http://localhost:5500.

    python servidor.py            (na pasta frontend)
    python servidor.py 8080       (outra porta)

Faz o mesmo que "python -m http.server", com uma diferença: manda o
navegador não guardar os arquivos. Com o http.server comum o navegador
reaproveita o CSS e o JavaScript por um tempo, e uma correção recém-
baixada do GitHub parece não ter efeito — a tela continua como antes até
alguém lembrar do Ctrl+F5. Em desenvolvimento, sempre a versão atual.
"""
import http.server
import os
import sys


class SemCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), SemCache)
    print(f"Front-end em http://localhost:{porta} — Ctrl+C para parar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nParado.")
