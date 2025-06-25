#!/bin/sh

set -eux

sudo groupadd -g $DOCKER_GID docker-host

sudo usermod -aG docker-host $(whoami)

exec sg docker-host -c "$@"

