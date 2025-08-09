FROM docker.io/golang:latest AS builder-golang

ENV CGO_ENABLED=0 \
    GOOS=linux

WORKDIR /usr/src/base

COPY go.mod go.sum ./

RUN go mod download

RUN --mount=type=bind,target=/usr/src/base \
    go build -a -o /usr/local/bin/ ./setup_user.go

FROM scratch

COPY --from=builder-golang /usr/local/bin/ /usr/local/bin
