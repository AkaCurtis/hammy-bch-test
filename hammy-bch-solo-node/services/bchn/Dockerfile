FROM debian:bookworm AS build

ARG BCHN_REPO=https://gitlab.com/bitcoin-cash-node/bitcoin-cash-node.git
ARG BCHN_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libtool autotools-dev automake pkg-config bsdmainutils python3 \
    libevent-dev libboost-system-dev libboost-filesystem-dev libboost-chrono-dev \
    libboost-test-dev libboost-thread-dev libminiupnpc-dev libzmq3-dev libssl-dev \
    libdb-dev libdb++-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch ${BCHN_REF} ${BCHN_REPO} .
RUN ./autogen.sh && \
    ./configure --without-gui --disable-tests --disable-bench --prefix=/opt/bchn && \
    make -j"$(nproc)" && \
    make install

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libevent-2.1-7 libboost-system1.74.0 libboost-filesystem1.74.0 \
    libboost-chrono1.74.0 libboost-thread1.74.0 libminiupnpc17 libzmq5 openssl \
    libdb5.3++ gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/bchn /opt/bchn
COPY entrypoint.sh /usr/local/bin/bchn-entrypoint.sh
ENV PATH="/opt/bchn/bin:${PATH}"

RUN chmod 755 /usr/local/bin/bchn-entrypoint.sh

USER 1000:1000
ENTRYPOINT ["/usr/local/bin/bchn-entrypoint.sh"]
