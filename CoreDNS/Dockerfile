FROM docker.io/golang:latest AS builder

ENV DEBCONF_NONINTERACTIVE_SEEN=true \
    DEBIAN_FRONTEND=noninteractive \
    DEBIAN_PRIORITY=critical

RUN set -eux; \
    apt-get update -qq \
    && apt-get install -qqy --no-install-recommends \
            ca-certificates libcap2-bin \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/coredns

COPY ./coredns .

RUN set -eux; \
    GOFLAGS="-buildvcs=false" make gen \
    && GOFLAGS="-buildvcs=false" make \
    && setcap cap_net_bind_service=+ep coredns \
    && ./coredns -version

RUN set -eux; \
    touch Corefile

FROM scratch

COPY --from=builder /usr/src/coredns/coredns /usr/local/bin/coredns
COPY --from=builder /usr/src/coredns/Corefile /etc/coredns/Corefile
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

CMD [ "coredns", "-conf", "/etc/coredns/Corefile" ]
