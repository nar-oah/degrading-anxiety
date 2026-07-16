#!/bin/sh

set -eu

RADICALE_UID=1000
RADICALE_GID=1000

mkdir -p \
  /auth \
  /var/lib/radicale/collections/collection-root

touch /auth/users

chown "${RADICALE_UID}:${RADICALE_GID}" \
  /auth \
  /auth/users \
  /var/lib/radicale \
  /var/lib/radicale/collections \
  /var/lib/radicale/collections/collection-root

chmod 0755 \
  /auth \
  /var/lib/radicale \
  /var/lib/radicale/collections \
  /var/lib/radicale/collections/collection-root

chmod 0640 /auth/users

exec su-exec \
  "${RADICALE_UID}:${RADICALE_GID}" \
  /app/bin/python \
  /app/bin/radicale \
  "$@"
