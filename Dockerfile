FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:0 \
    BROWSER_USER=browser \
    TZ=Asia/Baku

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium xvfb x11vnc novnc websockify nginx apache2-utils supervisor \
    fonts-liberation fonts-noto-color-emoji dbus-x11 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin browser \
    && mkdir -p /data /var/log/supervisor /run/nginx \
    && chown -R browser:browser /data /home/browser

COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /usr/local/bin/start-browser
RUN chmod 0755 /usr/local/bin/start-browser

EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/start-browser"]
