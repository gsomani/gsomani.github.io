#!/usr/bin/env python3
"""Tiny comment/upvote backend for the blog. Python stdlib + SQLite only.

Endpoints (JSON):
  GET  /api/comments/<thread>   -> [{id, name, message, date}]
  POST /api/comments/<thread>   {name, email?, message}
  GET  /api/upvotes/<thread>    -> {upvotes}
  POST /api/upvotes/<thread>    -> {upvotes}
The contact thread's messages are never returned by GET; read them in the DB.
"""
import json
import os
import re
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("COMMENT_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMMENT_PORT", "8080"))
DB_PATH = os.environ.get("COMMENT_DB", "comments.db")
ALLOWED_ORIGINS = os.environ.get(
    "COMMENT_ORIGINS", "https://gsomani.github.io"
).split(",")
CONTACT_THREAD = int(os.environ.get("COMMENT_CONTACT_THREAD", "3"))
TRUST_PROXY = os.environ.get("COMMENT_TRUST_PROXY") == "1"

MAX_BODY = 20_000
MAX_NAME = 80
MAX_EMAIL = 120
MAX_MESSAGE = 5_000
RATE_LIMIT_POSTS = 5
RATE_WINDOW_SECONDS = 600
UPVOTE_LIMIT = 20

ROUTE = re.compile(r"^/api/(comments|upvotes)/(\d{1,9})/?$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

dbLock = threading.Lock()
hits = {}


def openDb():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );
        CREATE INDEX IF NOT EXISTS commentsThread ON comments(thread);
        CREATE TABLE IF NOT EXISTS upvotes (
            thread INTEGER PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    return db


db = openDb()


def rateLimited(ip, limit, kind):
    now = time.time()
    key = (ip, kind)
    recent = [t for t in hits.get(key, []) if now - t < RATE_WINDOW_SECONDS]
    if len(recent) >= limit:
        hits[key] = recent
        return True
    recent.append(now)
    hits[key] = recent
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "CommentServer"

    def clientIp(self):
        if TRUST_PROXY:
            forwarded = self.headers.get("X-Forwarded-For", "")
            if forwarded:
                return forwarded.split(",")[-1].strip()
        return self.client_address[0]

    def send(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send(204)

    def route(self):
        match = ROUTE.match(self.path.split("?")[0])
        if not match:
            self.send(404, {"error": "not found"})
            return None
        return match.group(1), int(match.group(2))

    def do_GET(self):
        found = self.route()
        if not found:
            return
        kind, thread = found
        with dbLock:
            if kind == "upvotes":
                row = db.execute(
                    "SELECT count FROM upvotes WHERE thread=?", (thread,)
                ).fetchone()
                return self.send(200, {"upvotes": row[0] if row else 0})
            if thread == CONTACT_THREAD:
                return self.send(200, [])
            rows = db.execute(
                "SELECT id, name, message, createdAt FROM comments "
                "WHERE thread=? ORDER BY id",
                (thread,),
            ).fetchall()
        self.send(
            200,
            [{"id": r[0], "name": r[1], "message": r[2], "date": r[3]} for r in rows],
        )

    def readJson(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self.send(413, {"error": "body too large"})
            return None
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            data = None
        if not isinstance(data, dict):
            self.send(400, {"error": "invalid json"})
            return None
        return data

    def do_POST(self):
        found = self.route()
        if not found:
            return
        kind, thread = found
        ip = self.clientIp()

        if kind == "upvotes":
            if rateLimited(ip, UPVOTE_LIMIT, "upvote"):
                return self.send(429, {"error": "slow down"})
            with dbLock, db:
                db.execute(
                    "INSERT INTO upvotes(thread, count) VALUES(?, 1) "
                    "ON CONFLICT(thread) DO UPDATE SET count = count + 1",
                    (thread,),
                )
                count = db.execute(
                    "SELECT count FROM upvotes WHERE thread=?", (thread,)
                ).fetchone()[0]
            return self.send(200, {"upvotes": count})

        data = self.readJson()
        if data is None:
            return
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        message = str(data.get("message", "")).strip()
        if not name or not message:
            return self.send(400, {"error": "name and message required"})
        if len(name) > MAX_NAME or len(email) > MAX_EMAIL or len(message) > MAX_MESSAGE:
            return self.send(400, {"error": "field too long"})
        if email and not EMAIL.match(email):
            return self.send(400, {"error": "invalid email"})
        if thread == CONTACT_THREAD and not email:
            return self.send(400, {"error": "email required"})
        if rateLimited(ip, RATE_LIMIT_POSTS, "post"):
            return self.send(429, {"error": "too many comments, try later"})
        with dbLock, db:
            cur = db.execute(
                "INSERT INTO comments(thread, name, email, message) VALUES(?,?,?,?)",
                (thread, name, email, message),
            )
        self.send(201, {"id": cur.lastrowid})

    def log_message(self, fmt, *args):
        print("%s %s" % (self.clientIp(), fmt % args), flush=True)


if __name__ == "__main__":
    print(f"listening on {HOST}:{PORT}, db={DB_PATH}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
