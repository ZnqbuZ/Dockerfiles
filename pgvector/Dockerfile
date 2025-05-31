FROM docker.io/pgvector/pgvector:pg17

RUN set -eux; \
        /bin/echo -e '\
en_US.UTF-8 UTF-8\n\
fr_FR.UTF-8 UTF-8\n\
zh_CN.UTF-8 UTF-8\n' > /etc/locale.gen; \
        locale-gen
