# CinderX Performance Testing Environment
# Target real-env approximation:
# - openEuler 24.03 LTS SP1
# - GCC 14.2.x
# - CPython 3.14 built inside the image

FROM openeuler/openeuler:24.03-lts-sp1

ARG PYTHON_VERSION=3.14.0

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PATH=/opt/python314/bin:/opt/openEuler/gcc-toolset-14/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/python314/lib:/opt/openEuler/gcc-toolset-14/root/usr/lib64

RUN dnf install -y \
    --setopt=timeout=300 \
    --setopt=minrate=1 \
    --setopt=retries=20 \
    ca-certificates \
    cmake \
    curl \
    findutils \
    'gcc-toolset-14-gcc*' \
    'gcc-toolset-14-c++*' \
    'gcc-toolset-14-binutils*' \
    'gcc-toolset-14-libstdc++*' \
    git \
    make \
    patch \
    procps-ng \
    tar \
    wget \
    which \
    xz \
    bzip2-devel \
    expat-devel \
    gdbm-devel \
    libffi-devel \
    ncurses-devel \
    openssl-devel \
    readline-devel \
    sqlite-devel \
    tk-devel \
    xz-devel \
    zlib-devel \
    libuuid-devel \
    && mkdir -p /opt/openEuler/gcc-toolset-14/root/usr/lib64 \
    && ln -sf /usr/lib64/libgcc_s.so.1 /opt/openEuler/gcc-toolset-14/root/usr/lib64/libgcc_s.so.1 \
    && dnf clean all

RUN wget -q -O /tmp/Python-${PYTHON_VERSION}.tar.xz \
      https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz \
    && tar -xf /tmp/Python-${PYTHON_VERSION}.tar.xz -C /tmp \
    && printf '%s\n' 'int main(void) { return 0; }' > /tmp/cc-smoke.c \
    && gcc /tmp/cc-smoke.c -o /tmp/cc-smoke \
    && cd /tmp/Python-${PYTHON_VERSION} \
    && if ! ./configure \
         --prefix=/opt/python314 \
         --enable-shared \
         --with-ensurepip=install; then \
           status=$?; \
           echo '=== gcc -v ==='; \
           gcc -v; \
           echo '=== cc smoke ldd ==='; \
           ldd /tmp/cc-smoke || true; \
           echo '=== config.log tail ==='; \
           tail -n 200 config.log || true; \
           exit "$status"; \
       fi \
    && make -j"$(nproc)" \
    && make install \
    && ln -sf /opt/python314/bin/python3 /usr/local/bin/python3 \
    && ln -sf /opt/python314/bin/python3 /usr/local/bin/python \
    && ln -sf /opt/python314/bin/pip3 /usr/local/bin/pip3 \
    && ln -sf /opt/python314/bin/pip3 /usr/local/bin/pip \
    && rm -rf /tmp/Python-${PYTHON_VERSION} /tmp/Python-${PYTHON_VERSION}.tar.xz

# Create directories
RUN mkdir -p /root/benchmarks /results /opt/cpython-jit

# Install benchmark and runner scripts inside the image.
COPY scripts /scripts
COPY configs /scripts/configs
RUN chmod +x /scripts/*.sh /scripts/*.py

# Set up working directory
WORKDIR /root

# Default command
CMD ["/bin/bash"]
