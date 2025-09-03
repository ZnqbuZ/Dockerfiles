#!/bin/bash

set -euo pipefail

if [ -z "${PUSER:-}" ] && [ -z "${PUID:-}" ] && [ -z "${PGROUP:-}" ] && [ -z "${PGID:-}" ]; then
    export PUSER=root
    export PUID=0
    export PGROUP=root
    export PGID=0
fi

. <(setup-user --extra-group sudo --extra-gid "$DOCKER_GID") || exit 1

if [ "$PUID" -eq 0 ]; then
	echo "Running as root. Setting RUNNER_ALLOW_RUNASROOT to 1."
	export RUNNER_ALLOW_RUNASROOT=1
fi

if [ -f "$HOME/.credentials" ] && [ -f "$HOME/.credentials_rsaparams" ]; then
	echo "Credentials found, skip configuring."
else
	echo "No credentials found."
	echo "Installing actions runner..."
	rsync -a --info=progress2 --delete /runner/ "$HOME/"
	echo "Configuring..."
	gosu "$PUSER" "$HOME/config.sh" --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended --replace
fi

cd "$HOME"

export PATH="$HOME/.local/bin:$PATH"

exec gosu "$PUSER" bash -c "$@"
