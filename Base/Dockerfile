FROM docker.io/rust:latest AS builder-rust

ARG WORKDIR=/usr/src/base

ARG CRATE="setup-user"

WORKDIR ${WORKDIR}/${CRATE}

COPY ${CRATE}/Cargo.toml ${CRATE}/Cargo.lock ./

RUN set -eux; \
    mkdir src \
    && touch src/main.rs \
    && cargo build --release || true

RUN --mount=type=bind,source=${CRATE}/src,target=./src \
    set -eux; \
    cargo build --release \
    && cp target/release/${CRATE} /usr/local/bin/

FROM scratch

COPY --from=builder-rust /usr/local/bin/ /usr/local/bin
