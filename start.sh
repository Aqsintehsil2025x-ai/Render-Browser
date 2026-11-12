#!/bin/sh
set -eu

: "${BROWSER_USER:?Set BROWSER_USER in Render Environment}"
: "${BROWSER_PASSWORD:?Set BROWSER_PASSWORD in Render Environment}"

case "$BROWSER_USER" in
  *:*) echo "BROWSER_USER must not contain a colon" >&2; exit 1 ;;
esac

if [ "${#BROWSER_PASSWORD}" -lt 16 ]; then
  echo "BROWSER_PASSWORD must be at least 16 characters" >&2
  exit 1
fi

mkdir -p /data/chrome-profile /run/nginx /var/log/supervisor
chown -R browser:browser /data /home/browser

# Credentials are generated at container start and are never stored in the image.
htpasswd -Bbc /etc/nginx/.htpasswd "$BROWSER_USER" "$BROWSER_PASSWORD"
chmod 0600 /etc/nginx/.htpasswd

AI_SERVICE_URL="${AI_SERVICE_URL:-http://127.0.0.1:10001}"
AI_API_KEY="${AI_API_KEY:-not-configured}"
export AI_SERVICE_URL AI_API_KEY

# Substitute only the two application settings; preserve Nginx runtime variables.
envsubst '${AI_SERVICE_URL} ${AI_API_KEY}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
