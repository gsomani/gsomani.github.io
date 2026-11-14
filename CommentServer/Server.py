#!/usr/bin/env python3
"""Tiny comment/upvote backend for the blog. Python stdlib + SQLite only.

Endpoints (JSON):
  GET  /api/comments/<thread>   -> [{id, name, message, date}]
  POST /api/comments/<thread>   {name, email?, message}
  GET  /api/upvotes/<thread>    -> {upvotes}
  POST /api/upvotes/<thread>    -> {upvotes}
The contact thread's messages are never returned by GET; read them in the DB.
"""
import hashlib
import ipaddress
import json
import os
import secrets
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
# Only these thread ids (the `issue:` values in page front matter) are accepted.
THREADS = {
    int(t) for t in os.environ.get("COMMENT_THREADS", "2,3,5").split(",") if t.strip()
}
THREADS.add(CONTACT_THREAD)
TRUST_PROXY = os.environ.get("COMMENT_TRUST_PROXY") == "1"

MAX_BODY = 20_000
MAX_NAME = 80
MAX_EMAIL = 120
MAX_MESSAGE = 5_000
RATE_LIMIT_POSTS = 5
RATE_WINDOW_SECONDS = 600
UPVOTE_LIMIT = 20
GLOBAL_POSTS_PER_HOUR = int(os.environ.get("COMMENT_GLOBAL_PER_HOUR", "60"))
MAX_TRACKED_KEYS = 10_000

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
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS upvotes (
            thread INTEGER PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    columns = [row[1] for row in db.execute("PRAGMA table_info(comments)")]
    if "ipHash" not in columns:
        db.execute("ALTER TABLE comments ADD COLUMN ipHash TEXT NOT NULL DEFAULT ''")
    db.execute("CREATE INDEX IF NOT EXISTS commentsIp ON comments(ipHash, createdAt)")
    db.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES('salt', ?)",
        (secrets.token_hex(16),),
    )
    db.commit()
    return db


db = openDb()
SALT = db.execute("SELECT value FROM meta WHERE key='salt'").fetchone()[0]


def ipKey(ip):
    """Normalise an address; IPv6 is grouped by /64 so rotating addresses doesn't help."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if addr.version == 6:
        if addr.ipv4_mapped:
            return str(addr.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/64", strict=False).network_address)
    return str(addr)


def ipHash(ip):
    return hashlib.sha256((SALT + ipKey(ip)).encode()).hexdigest()[:16]


def isoTime(secondsAgo):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - secondsAgo))


def rateLimited(ip, limit, kind):
    now = time.time()
    if len(hits) > MAX_TRACKED_KEYS:
        for oldKey in [k for k, v in hits.items() if not v or now - v[-1] >= RATE_WINDOW_SECONDS]:
            del hits[oldKey]
    key = (ipKey(ip), kind)
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

    def originAllowed(self):
        return self.headers.get("Origin", "") in ALLOWED_ORIGINS

    def do_OPTIONS(self):
        self.send(204)

    def route(self):
        match = ROUTE.match(self.path.split("?")[0])
        if not match:
            self.send(404, {"error": "not found"})
            return None
        thread = int(match.group(2))
        if thread not in THREADS:
            self.send(404, {"error": "unknown thread"})
            return None
        return match.group(1), thread

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
        if not self.originAllowed():
            return self.send(403, {"error": "origin not allowed"})

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

        contentType = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if contentType != "application/json":
            return self.send(415, {"error": "content-type must be application/json"})
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
        author = ipHash(ip)
        with dbLock, db:
            perIp = db.execute(
                "SELECT COUNT(*) FROM comments WHERE ipHash=? AND createdAt>?",
                (author, isoTime(RATE_WINDOW_SECONDS)),
            ).fetchone()[0]
            overall = db.execute(
                "SELECT COUNT(*) FROM comments WHERE createdAt>?", (isoTime(3600),)
            ).fetchone()[0]
            if perIp >= RATE_LIMIT_POSTS or overall >= GLOBAL_POSTS_PER_HOUR:
                return self.send(429, {"error": "too many comments, try later"})
            cur = db.execute(
                "INSERT INTO comments(thread, name, email, message, ipHash) "
                "VALUES(?,?,?,?,?)",
                (thread, name, email, message, author),
            )
        self.send(201, {"id": cur.lastrowid})

    def log_message(self, fmt, *args):
        print("%s %s" % (self.clientIp(), fmt % args), flush=True)


if __name__ == "__main__":
    print(f"listening on {HOST}:{PORT}, db={DB_PATH}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
