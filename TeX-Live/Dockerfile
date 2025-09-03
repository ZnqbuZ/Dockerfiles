FROM docker.io/texlive/texlive:latest

RUN set -eux; \
	tlmgr path add

RUN set -eux; \
	chsh -s /usr/bin/fish

RUN set -eux; \
	apt-get update -qq \
	&& apt-get install tini fish ssh syncthing fonts-arphic-ukai fonts-arphic-uming fonts-lxgw-wenkai fonts-noto-cjk-extra fonts-smiley-sans fonts-wqy-microhei fonts-wqy-zenhei -y --no-install-recommends \
	&& rm -rf /var/lib/apt/lists/*

RUN set -eux; \
	git clone https://github.com/ZnqbuZ/LaTeX.git ~/LaTeX \
	&& sh -eux ~/LaTeX/font-cache.sh \
	&& sh -eux ~/LaTeX/build.sh

COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint

ENTRYPOINT [ "tini", "--", "/usr/local/bin/entrypoint" ]
