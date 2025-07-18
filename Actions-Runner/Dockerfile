FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV RUNNER_MANUALLY_TRAP_SIG=1
ENV ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT=1

RUN set -eux; \
    install -m 0755 -d /etc/apt/keyrings \
    && install -m 0755 -d /etc/apt/sources.list.d 

RUN set -eux; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        tini gosu sudo \ 
        lsb-release gpg-agent software-properties-common \
        ca-certificates curl wget rsync \
        git build-essential \
        jq unzip \
    && rm -rf /var/lib/apt/lists/*

RUN  set -eux; \
    echo "root       ALL=(ALL:ALL) ALL" > /etc/sudoers \
    && echo "%sudo      ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && echo 'Defaults   env_keep += "DEBIAN_FRONTEND"' >> /etc/sudoers \
	&& echo 'Defaults   env_keep += "HOME"' >> /etc/sudoers

RUN set -eux; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv pipx \
    && rm -rf /var/lib/apt/lists/* \
    && pipx install pipx \
    && apt-get autoremove --purge -y pipx \
    && ~/.local/bin/pipx install pipx --global \
    && /usr/local/bin/pipx uninstall pipx \
    && /usr/local/bin/pipx ensurepath --global

RUN set -eux; \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod a+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin skopeo \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

RUN set -eux; \
    LATEST_TAG=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name); \
    LATEST_VERSION=${LATEST_TAG#v}; \
    mkdir /runner \
    && wget -qO- https://github.com/actions/runner/releases/download/${LATEST_TAG}/actions-runner-linux-x64-${LATEST_VERSION}.tar.gz \
    | tar xz -C /runner

ENTRYPOINT [ "tini", "--", "/usr/local/bin/entrypoint" ]

CMD [ "./run.sh" ]

