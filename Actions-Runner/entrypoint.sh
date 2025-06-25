#!/bin/sh

sudo groupadd -g $DOCKER_GID docker-host

sudo usermod -aG docker-host $(whoami)

exec sg docker-host -c './config.sh --url $RUNNER_URL --token $RUNNER_TOKEN --name $RUNNER_NAME --unattended --replace && ./run.sh
