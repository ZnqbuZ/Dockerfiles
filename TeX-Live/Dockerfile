FROM docker.io/texlive/texlive:latest

RUN set -eux; \
	tlmgr path add

RUN set -eux; \
	apt update \
	&& apt install fish ssh syncthing fonts-noto-cjk-extra -y --no-install-recommends

RUN set -eux; \
	chsh -s /usr/bin/fish

RUN set -eux; \
	git clone https://github.com/ZnqbuZ/LaTeX.git ~/LaTeX \
	&& sh ~/LaTeX/font-cache.sh \
	&& sh ~/LaTeX/build.sh

RUN set -eux; \
	rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

ENTRYPOINT [ "entrypoint" ]
