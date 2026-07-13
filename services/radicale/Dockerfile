FROM kozea/radicale:3.7

USER root

RUN apk add --no-cache su-exec \
  && mkdir -p /etc/radicale

COPY config /etc/radicale/config
COPY entrypoint.sh /usr/local/bin/radicale-entrypoint

RUN chmod 0644 /etc/radicale/config \
  && chmod 0755 /usr/local/bin/radicale-entrypoint

ENTRYPOINT ["/usr/local/bin/radicale-entrypoint"]

CMD ["--hosts", "0.0.0.0:5232,[::]:5232"]
