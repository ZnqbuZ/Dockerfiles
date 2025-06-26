#!/bin/bash

set -euxo pipefail

groupadd -g $DOCKER_GID -f docker-host

adduser --disabled-password --gecos "" --uid $RUNNER_UID --home $RUNNER_HOME --no-create-home runner

usermod -aG sudo,docker-host runner

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

chown runner:runner -R $RUNNER_HOME
cd $RUNNER_HOME

if [ $IS_INSTALLED -eq 0 ]; then
	echo "Configuring..."
	gosu runner ./config.sh --url $RUNNER_URL --token $RUNNER_TOKEN --name $RUNNER_NAME --unattended --replace
fi

exec gosu runner bash -c "$@"

