# CinderX Performance Testing Environment
# Target real-env approximation:
# - openEuler 24.03 LTS SP3
# - CPython built with GCC 12.3.1
# - CinderX built with GCC 14.x
# - CPython 3.14 built inside the image

FROM openeuler/openeuler:24.03-lts-sp3

ARG PYTHON_VERSION=3.14.3

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV CPYTHON_GCC_VERSION=12.3.1

RUN dnf install -y \
    --setopt=timeout=300 \
    --setopt=minrate=1 \
    --setopt=retries=20 \
    ca-certificates \
    cmake \
    curl \
    findutils \
    gcc \
    gcc-c++ \
    binutils \
    libstdc++ \
    libstdc++-devel \
    'gcc-toolset-14-gcc*' \
    'gcc-toolset-14-gcc-c++' \
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
    && test "$(gcc -dumpfullversion -dumpversion)" = "$CPYTHON_GCC_VERSION" \
    && printf '%s\n' 'int main(void) { return 0; }' > /tmp/cc-smoke.c \
    && /usr/bin/gcc /tmp/cc-smoke.c -o /tmp/cc-smoke \
    && cd /tmp/Python-${PYTHON_VERSION} \
    && if ! CC=/usr/bin/gcc CXX=/usr/bin/g++ ./configure \
         --enable-optimizations \
         --with-lto; then \
           status=$?; \
           echo '=== /usr/bin/gcc -v ==='; \
           /usr/bin/gcc -v; \
           echo '=== cc smoke ldd ==='; \
           ldd /tmp/cc-smoke || true; \
           echo '=== config.log tail ==='; \
           tail -n 200 config.log || true; \
           exit "$status"; \
       fi \
    && make -j"$(nproc)" \
    && make install \
    && /usr/local/bin/python3 -c "import pathlib, sysconfig; assert not int(sysconfig.get_config_var('Py_ENABLE_SHARED') or 0); libdir = pathlib.Path(sysconfig.get_config_var('LIBDIR') or '/usr/local/lib'); shared = list(libdir.glob('libpython3.14*.so*')); assert not shared, shared" \
    && ln -sf /usr/local/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/local/bin/pip3 /usr/local/bin/pip \
    && rm -rf /tmp/Python-${PYTHON_VERSION} /tmp/Python-${PYTHON_VERSION}.tar.xz

ENV PATH=/opt/openEuler/gcc-toolset-14/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/openEuler/gcc-toolset-14/root/usr/lib64

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
