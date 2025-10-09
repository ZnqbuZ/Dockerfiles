ARG PROJECT=dnscrypt-proxy
ARG WORKDIR=/usr/src/dnscrypt-proxy

FROM docker.io/golang:latest AS builder

ARG PROJECT
ARG WORKDIR

ENV DEBCONF_NONINTERACTIVE_SEEN=true \
    DEBIAN_FRONTEND=noninteractive \
    DEBIAN_PRIORITY=critical

WORKDIR ${WORKDIR}

COPY ./${PROJECT}/ .

RUN set -eux; \
    export CGO_ENABLED=0 \
    && mkdir build \
    && go build -v -ldflags="-s -w" -mod vendor -o build/${PROJECT} ./dnscrypt-proxy \
    && build/${PROJECT} -version

FROM scratch

ARG PROJECT
ARG WORKDIR

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder ${WORKDIR}/build/${PROJECT} /usr/local/bin/${PROJECT}
COPY --from=builder ${WORKDIR}/dnscrypt-proxy/example-dnscrypt-proxy.toml /etc/dnscrypt-proxy/dnscrypt-proxy.toml

ENTRYPOINT [ "dnscrypt-proxy" ]

CMD [ "-config", "/etc/dnscrypt-proxy/dnscrypt-proxy.toml" ]

