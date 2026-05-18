FROM debian:bookworm AS build

ARG BCHN_REPO=https://gitlab.com/bitcoin-cash-node/bitcoin-cash-node.git
ARG BCHN_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential cmake ninja-build pkg-config python3 bison \
    libevent-dev libboost-system-dev libboost-filesystem-dev libboost-chrono-dev \
    libboost-thread-dev libboost-test-dev libminiupnpc-dev libnatpmp-dev libzmq3-dev libssl-dev libgmp-dev \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch ${BCHN_REF} ${BCHN_REPO} .
RUN cmake -S . -B build -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/opt/bchn \
    -DBUILD_BITCOIN_WALLET=OFF \
    -DBUILD_GUI=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_BENCH=OFF \
    -DENABLE_MAN=OFF && \
    cmake --build build && \
    cmake --install build

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libevent-2.1-7 libboost-system1.74.0 libboost-filesystem1.74.0 \
    libboost-chrono1.74.0 libboost-thread1.74.0 libminiupnpc17 libnatpmp1 libzmq5 openssl \
    libgmp10 gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/bchn /opt/bchn
COPY entrypoint.sh /usr/local/bin/bchn-entrypoint.sh
ENV PATH="/opt/bchn/bin:${PATH}"

RUN chmod 755 /usr/local/bin/bchn-entrypoint.sh

USER 1000:1000
ENTRYPOINT ["/usr/local/bin/bchn-entrypoint.sh"]
