ARG PROJECT=coredns
ARG WORKDIR=/usr/src/coredns

FROM docker.io/golang:latest AS builder

ARG PROJECT
ARG WORKDIR

ENV DEBCONF_NONINTERACTIVE_SEEN=true \
    DEBIAN_FRONTEND=noninteractive \
    DEBIAN_PRIORITY=critical

RUN set -eux; \
    apt-get update -qq \
    && apt-get install -qqy --no-install-recommends \
            ca-certificates libcap2-bin libunbound-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR ${WORKDIR}

COPY ./${PROJECT}/ .

RUN set -eux; \
    export GOFLAGS="-buildvcs=false" CGO_ENABLED=1 \
    && make gen \
    && make \
    && setcap cap_net_bind_service=+ep coredns \
    && ./coredns -version

RUN set -eux; \
    mkdir /usr/lib/coredns \
    && ldd ./coredns \
        | tr ' ' '\n' \
        | sed -En 's/^[[:space:]]*(\/.*)$/\1/p' \
        | sort -u \
        | xargs -I{} cp --parents "{}" /usr/lib/coredns

RUN set -eux; \
    touch Corefile

FROM scratch

ARG PROJECT
ARG WORKDIR

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/lib/coredns/ /
COPY --from=builder ${WORKDIR}/coredns /usr/local/bin/coredns
COPY --from=builder ${WORKDIR}/Corefile /etc/coredns/Corefile

ENTRYPOINT [ "coredns" ]

CMD [ "-conf", "/etc/coredns/Corefile" ]

