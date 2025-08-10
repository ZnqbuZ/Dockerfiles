FROM docker.io/rust:latest AS builder-rust

ARG WORKDIR=/usr/src/base

ARG CRATE="setup-user"

WORKDIR ${WORKDIR}/${CRATE}

COPY ${CRATE}/Cargo.toml ${CRATE}/Cargo.lock ./

RUN set -eux; \
    mkdir src \
    && echo "fn main() {}" > src/main.rs \
    && cargo build --release \
    && rm -rf src

RUN --mount=type=bind,source=${CRATE}/src,target=./src \
    cargo build --release \
    && cp target/release/${CRATE} /usr/local/bin/

FROM scratch

COPY --from=builder-rust /usr/local/bin/ /usr/local/bin
