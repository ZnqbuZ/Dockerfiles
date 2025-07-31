FROM docker.io/python:alpine

RUN set -eux; \
	apk update \
	&& apk add tini \
	&& rm -rf /var/cache/apk/*

RUN set -eux; \
	python3 -m pip install --no-cache-dir requests

COPY entrypoint.py /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

ENTRYPOINT [ "tini", "--", "/usr/local/bin/entrypoint" ]
