FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV RUNNER_MANUALLY_TRAP_SIG=1
ENV ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT=1

RUN set -eux; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        tini \
        lsb-release gpg-agent software-properties-common \
        ca-certificates curl wget \
	sudo \
        build-essential \
        git \
        jq \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin skopeo

RUN set -eux; \
    adduser --disabled-password --gecos "" --uid 1001 runner \
    && usermod -aG sudo runner \
    && echo "root	ALL=(ALL:ALL) ALL" > /etc/sudoers \
    && echo "%sudo	ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && echo "Defaults	env_keep += \"DEBIAN_FRONTEND\"" >> /etc/sudoers

COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

WORKDIR /home/runner

RUN set -eux; \
    LATEST_TAG=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name); \
    LATEST_VERSION=${LATEST_TAG#v}; \
    wget -qO- https://github.com/actions/runner/releases/download/${LATEST_TAG}/actions-runner-linux-x64-${LATEST_VERSION}.tar.gz \
    | tar xz -C . --strip-components=1

USER runner

ENTRYPOINT [ "tini", "--", "/usr/local/bin/entrypoint" ]

CMD [ "./config.sh --url $RUNNER_URL --token $RUNNER_TOKEN --name $RUNNER_NAME --unattended --replace && ./run.sh" ]

