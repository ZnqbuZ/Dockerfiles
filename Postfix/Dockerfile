FROM docker.io/alpine:latest

RUN set -eux; \
	apk update \
	&& apk add postfix postfix-pgsql \
	&& rm -rf /var/cache/apk/*

COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

EXPOSE 25

ENTRYPOINT [ "tini", "--", "/usr/local/bin/entrypoint" ]
