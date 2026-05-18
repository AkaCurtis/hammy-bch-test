FROM debian:bookworm AS build

ARG CKPOOL_REPO=https://github.com/ctubio/ckpool.git
ARG CKPOOL_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential autoconf automake libtool pkg-config \
    libcurl4-openssl-dev libjansson-dev libssl-dev zlib1g-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch ${CKPOOL_REF} ${CKPOOL_REPO} .
RUN ./autogen.sh && \
    ./configure --prefix=/opt/ckpool && \
    make -j"$(nproc)" && \
    make install

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libcurl4 libjansson4 libssl3 zlib1g gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/ckpool /opt/ckpool
COPY entrypoint.sh /usr/local/bin/ckpool-entrypoint.sh
ENV PATH="/opt/ckpool/bin:${PATH}"

RUN chmod 755 /usr/local/bin/ckpool-entrypoint.sh

USER 1000:1000
ENTRYPOINT ["/usr/local/bin/ckpool-entrypoint.sh"]
