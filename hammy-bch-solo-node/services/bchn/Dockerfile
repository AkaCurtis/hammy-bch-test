FROM debian:bookworm AS build

ARG BCHN_REPO=https://gitlab.com/bitcoin-cash-node/bitcoin-cash-node.git
ARG BCHN_REF=v29.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential cmake ninja-build pkg-config python3 bison \
    libevent-dev libboost-system-dev libboost-filesystem-dev libboost-chrono-dev \
    libboost-thread-dev libboost-test-dev libminiupnpc-dev libnatpmp-dev libzmq3-dev \
    libssl-dev libgmp-dev libdb++-dev libsqlite3-dev \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git ls-remote --heads --tags ${BCHN_REPO} ${BCHN_REF} && \
    git clone --depth 1 --branch ${BCHN_REF} ${BCHN_REPO} . && \
    ls -la && \
    echo "=== CMake version ===" && \
    cmake --version

RUN echo "=== Starting CMake configuration ===" && \
    cmake -S . -B build -GNinja \
    --debug-output \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/opt/bchn \
    -DBUILD_BITCOIN_WALLET=OFF \
    -DBUILD_BITCOIN_QT=OFF \
    -DENABLE_MAN=OFF || \
    (echo "CMake configuration failed. Checking for CMakeLists.txt:" && \
     ls -la CMakeLists.txt && \
     cat CMakeLists.txt | head -50 && \
     exit 1)

RUN echo "=== Starting build ===" && \
    cmake --build build

RUN echo "=== Starting install ===" && \
    cmake --install build

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libevent-2.1-7 libboost-system1.74.0 libboost-filesystem1.74.0 \
    libboost-chrono1.74.0 libboost-thread1.74.0 libminiupnpc17 libnatpmp1 libzmq5 openssl \
    libgmp10 libgmpxx4ldbl gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/bchn /opt/bchn
COPY entrypoint.sh /usr/local/bin/bchn-entrypoint.sh
ENV PATH="/opt/bchn/bin:${PATH}"

RUN chmod 755 /usr/local/bin/bchn-entrypoint.sh

USER 1000:1000
ENTRYPOINT ["/usr/local/bin/bchn-entrypoint.sh"]
