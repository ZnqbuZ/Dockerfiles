#!/bin/bash

set -euxo pipefail

if [ -z "$USER" ] && [ -z "$UID" ] && [ -z "$GROUP" ] && [ -z "$GID" ]; then
    USER=root
    UID=0
    GROUP=root
    GID=0
fi

setup_user --extra-group sudo --extra-gid "$DOCKER_GID"

if [ -f "$HOME/.credentials" ] && [ -f "$HOME/.credentials_rsaparams" ]; then
	echo "Credentials found, skip configuring."
else
	echo "No credentials found."
	echo "Installing actions runner..."
	rsync -a --info=progress2 --delete /runner/ "$HOME"/
	echo "Configuring..."
	gosu "$USER" "$HOME"/config.sh --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended --replace
fi

cd "$HOME"

exec gosu "$USER" bash -c "$@"
