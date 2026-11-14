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
