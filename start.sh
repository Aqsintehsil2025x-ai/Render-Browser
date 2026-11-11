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

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
