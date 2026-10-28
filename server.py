"""HACKATOHM MVP — servidor de demonstracao local (nao industrial). Python >=3.10."""
from __future__ import annotations

import csv
import io
import json
import math
import re
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
DB = BASE / "leituras.sqlite3"
PORT = int(os.environ.get("HACKATOHM_PORT", "8000"))
HOST = os.environ.get("HACKATOHM_HOST", "127.0.0.1")
API_KEY = os.environ.get("HACKATOHM_API_KEY", "")
# Limites SO PARA DEMONSTRACAO. NUNCA UTILIZAR DIRETAMENTE EM EQUIPAMENTO INDUSTRIAL.
LIMITE_ATENCAO_C = 70.0
LIMITE_CRITICO_C = 85.0
ESCOVAS = ("E01", "E02", "E03", "E04")


def status(temperatura: float, ambiente: float) -> str:
    if temperatura >= LIMITE_CRITICO_C:
        return "critico"
    if temperatura >= LIMITE_ATENCAO_C:
        return "atencao"
    return "normal"


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horario TEXT NOT NULL,
            escova TEXT NOT NULL,
            temperatura_c REAL NOT NULL,
            ambiente_c REAL NOT NULL,
            origem TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_leituras_escova_hora ON leituras(escova, id)")
        qty = c.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
        if qty == 0:
            seed(c)


def seed(c):
    rng = random.Random(44)
    start = datetime.now(timezone.utc) - timedelta(minutes=24)
    for n in range(25):
        at = (start + timedelta(minutes=n)).isoformat(timespec="seconds")
        for j, escova in enumerate(ESCOVAS):
            temp = (43 + j * 2.6 + 0.12 * n + rng.uniform(-1.3, 1.3))
            if escova == "E03":
                temp += max(0, n - 15) * 2.75
            c.execute("INSERT INTO leituras(horario,escova,temperatura_c,ambiente_c,origem) VALUES (?,?,?,?,?)",
                      (at, escova, round(temp, 2), round(30 + rng.uniform(-0.8, 0.8), 2), "simulado"))


def add_reading(data):
    brush = str(data.get("escova", "")).upper()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", brush):
        raise ValueError("'escova' deve ter 1 a 48 caracteres")
    try:
        t = float(data["temperatura_c"])
        a = float(data["ambiente_c"])
    except (TypeError, ValueError, KeyError):
        raise ValueError("'temperatura_c' e 'ambiente_c' devem ser numericos")
    if not (math.isfinite(t) and math.isfinite(a) and -40 <= t <= 380 and -40 <= a <= 125):
        raise ValueError("temperaturas fora do intervalo permitido para a demonstracao")
    origem = "sensor" if data.get("origem") != "simulado" else "simulado"
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as c:
        c.execute("INSERT INTO leituras(horario,escova,temperatura_c,ambiente_c,origem) VALUES (?,?,?,?,?)",
                  (at, brush, round(t,2), round(a,2), origem))
    return {"escova": brush, "temperatura_c": t, "ambiente_c": a, "estado": status(t,a)}


def overview():
    with connect() as c:
        all_rows = c.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 2400").fetchall()
    values = {}
    for r in all_rows:
        b = r["escova"]
        values.setdefault(b, []).append(dict(r))
    result = []
    for b in sorted(values):
        group = list(reversed(values[b][:60]))
        last = group[-1]
        latest = last["temperatura_c"]
        amb = last["ambiente_c"]
        # Inclui diferenca temporal como METADADO para a interface; nao e diagnostico validado.
        result.append({"escova": b, "temperatura_c": latest,
                       "ambiente_c": amb, "delta_c": round(latest-amb,1),
                       "estado": status(latest, amb), "horario": last["horario"],
                       "origem": last["origem"], "historico": group})
    return {"escovas": result, "amostras": len(all_rows), "limites_demo":
            {"atencao_c": LIMITE_ATENCAO_C, "critico_c": LIMITE_CRITICO_C},
            "observacao": "Limites ilustrativos; nao validados nem seguros para controle industrial."}


def demo_aquecimento():
    rng = random.Random()
    with connect() as c:
        previous = c.execute("SELECT temperatura_c FROM leituras WHERE escova=? ORDER BY id DESC LIMIT 1", ("E03",)).fetchone()
        start = previous[0] if previous else 48
        for i in range(10):
            t = max(start + (i+1)*max(2.0, (92-start)/10), start + 2*(i+1))
            c.execute("INSERT INTO leituras(horario,escova,temperatura_c,ambiente_c,origem) VALUES (?,?,?,?,?)",
                      (datetime.now(timezone.utc).isoformat(timespec="seconds"), "E03", round(t+rng.uniform(-0.3,0.3),2), 31.0, "simulado"))


class Handler(BaseHTTPRequestHandler):
    def json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            data = (BASE/"index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/overview":
            self.json_response(overview())
        elif path == "/api/export.csv":
            with connect() as c:
                rows = c.execute("SELECT horario,escova,temperatura_c,ambiente_c,origem FROM leituras ORDER BY id").fetchall()
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(["horario_utc", "escova", "temperatura_c", "ambiente_c", "origem"])
            for row in rows:
                writer.writerow(row)
            raw = out.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="hackatohm_leituras.csv"')
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        else:
            self.json_response({"erro": "Rota inexistente"}, 404)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/reading" and API_KEY and self.headers.get("X-API-Key") != API_KEY:
            return self.json_response({"erro": "Chave da API invalida"}, 401)
        if route in ("/api/demo", "/api/reset_demo") and self.client_address[0] not in ("127.0.0.1", "::1"):
            return self.json_response({"erro": "Acoes simuladas disponiveis somente no servidor local"}, 403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.json_response({"erro": "Content-Length invalido"}, 400)
        if length < 0:
            return self.json_response({"erro": "Content-Length invalido"}, 400)
        if length > 4096:
            return self.json_response({"erro": "Payload excessivo"}, 413)
        try:
            data = json.loads(self.rfile.read(length)) if length else {}
            if not isinstance(data, dict):
                raise ValueError("Envie objeto JSON")
            route = urlparse(self.path).path
            if route == "/api/reading":
                return self.json_response(add_reading(data), 201)
            if route == "/api/demo":
                demo_aquecimento()
                return self.json_response({"ok": True})
            if route == "/api/reset_demo":
                with connect() as c:
                    c.execute("DELETE FROM leituras")
                    seed(c)
                return self.json_response({"ok": True})
            return self.json_response({"erro": "Rota inexistente"}, 404)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.json_response({"erro": str(exc)}, 400)


if __name__ == "__main__":
    init_db()
    print(f"HACKATOHM demo: http://{HOST}:{PORT} | sem uso industrial | CTRL+C para parar")
    if HOST != '127.0.0.1' and not API_KEY:
        print('AVISO: rede habilitada sem autenticacao. Configure HACKATOHM_API_KEY antes de compartilhar.')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
