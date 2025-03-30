FROM docker.io/python:alpine

RUN set -eux; \
	python3 -m pip install --no-cache-dir requests DeepDiff

COPY entrypoint.py /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

ENTRYPOINT [ "entrypoint" ]
