#!/bin/bash

set -euxo pipefail

USER="runner"
GROUP="runner"

GID=${GID:-${UID:-}}

if [ -n "${GID:-}" ]; then
    echo "GID set to $GID."
    EXISTING_GROUP=$(getent group "$GID" | cut -d: -f1 || true)
    if [ -n "$EXISTING_GROUP" ]; then
        GROUP="$EXISTING_GROUP"
        echo "Using existing group '$GROUP' with GID $GID."
    else
        echo "Creating group '$GROUP' with GID $GID."
        addgroup --gid "$GID" "$GROUP"
    fi
else
    GID=0
	GROUP="root"
    echo "GID is not set, using 0."
fi

if [ -n "${UID:-}" ]; then
    echo "UID set to $UID."
    EXISTING_USER=$(getent passwd "$UID" | cut -d: -f1 || true)
    if [ -n "$EXISTING_USER" ]; then
        USER="$EXISTING_USER"
        echo "Using existing user '$USER' with UID $UID."
    else
        echo "Creating user '$USER' with UID $UID."
        adduser --disabled-password --gecos "" --uid "$UID" --gid "$GID" --home "$HOME" --no-create-home "$USER"
        usermod -aG sudo "$USER"
    fi
else
    UID=0
	USER="root"
    echo "UID is not set, using 0."
fi

if [ $UID -eq 0 ]; then
	echo "Running as root. Setting RUNNER_ALLOW_RUNASROOT to 1."
	export RUNNER_ALLOW_RUNASROOT=1
fi

mkdir -p "$HOME"
chown -R "$USER":"$GROUP" "$HOME"

groupadd -g $DOCKER_GID -f docker-host
usermod -aG docker-host $USER

if [ -f "$HOME/.credentials" ] && [ -f "$HOME/.credentials_rsaparams" ]; then
	echo "Credentials found, skip configuring."
else
	echo "No credentials found."
	echo "Installing actions runner..."
	rsync -a --info=progress2 --delete /runner/ $HOME/
	echo "Configuring..."
	gosu $USER ./config.sh --url $RUNNER_URL --token $RUNNER_TOKEN --name $RUNNER_NAME --unattended --replace
fi

cd $HOME

exec gosu $USER bash -c "$@"
