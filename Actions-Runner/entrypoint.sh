#!/bin/bash

set -euxo pipefail

echo "Will run in ${RUNNER_HOME}"

groupadd -g $DOCKER_GID -f docker-host

if [ -n "${RUNNER_UID:-}" ]; then
	if [ -z "${RUNNER_USERNAME:-}" ]; then
		RUNNER_USERNAME=runner
		echo "RUNNER_USERNAME is not set, using default: $RUNNER_USERNAME"
	fi

	adduser --disabled-password --gecos "" --uid $RUNNER_UID --home $RUNNER_HOME --no-create-home $RUNNER_USERNAME
	usermod -aG sudo,docker-host $RUNNER_USERNAME
else
	RUNNER_UID=0
	RUNNER_USERNAME=root
	export RUNNER_ALLOW_RUNASROOT=1
fi

echo "root       ALL=(ALL:ALL) ALL" > /etc/sudoers
echo "%sudo      ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers
echo "Defaults   env_keep += \"DEBIAN_FRONTEND\"" >> /etc/sudoers

IS_INSTALLED=0

if [ -f "$RUNNER_HOME/.credentials" ] && [ -f "$RUNNER_HOME/.credentials_rsaparams" ]; then
	echo "Credentials found, skip configuring."
	IS_INSTALLED=1
else
	echo "No credentials found."
	echo "Installing actions runner..."
	rsync -a --info=progress2 --delete /runner/ $RUNNER_HOME/
fi

chown $RUNNER_USERNAME:$RUNNER_USERNAME -R $RUNNER_HOME
cd $RUNNER_HOME

if [ $IS_INSTALLED -eq 0 ]; then
	echo "Configuring..."
	gosu $RUNNER_USERNAME ./config.sh --url $RUNNER_URL --token $RUNNER_TOKEN --name $RUNNER_NAME --unattended --replace
fi

exec gosu $RUNNER_USERNAME bash -c "$@"
