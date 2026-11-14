# CommentServer

Stdlib-only Python + SQLite backend for blog comments, upvotes and the contact form.

## Run on the BeagleBone
    sudo mkdir -p /opt/CommentServer && sudo cp Server.py /opt/CommentServer/
    sudo cp CommentServer.service /etc/systemd/system/
    sudo systemctl enable --now CommentServer

Listens on 127.0.0.1:8080. Put it behind HTTPS (the site is https, so browsers
block plain-http calls): a Cloudflare Tunnel, or Caddy/nginx with a certificate.
Then set `commentApi` in `_config.yml` to that public URL.

Env vars: COMMENT_PORT, COMMENT_DB, COMMENT_ORIGINS (comma-separated allowed
origins), COMMENT_CONTACT_THREAD (default 3, never served publicly),
COMMENT_TRUST_PROXY=1 when behind a reverse proxy (uses X-Forwarded-For for rate limits).

## Read contact messages
    sqlite3 /var/lib/commentserver/comments.db "select createdAt,name,email,message from comments where thread=3"

## Thread ids
Only ids listed in `COMMENT_THREADS` (service file, default `2,3,5`) are accepted. When you
add a post with a new `issue:` value, add it there and run `sudo systemctl restart CommentServer`.

## Abuse protection
- POSTs must come from an allowed `Origin` with `Content-Type: application/json`.
- Per-IP limit: 5 comments / 10 min (IPv6 grouped by /64, stored as a salted hash so it survives
  restarts); global cap 60 comments / hour (`COMMENT_GLOBAL_PER_HOUR`).
- nginx adds request-rate, connection and body-size limits (see `NginxLimits.conf`).
