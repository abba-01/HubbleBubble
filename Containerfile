FROM quay.io/pypa/manylinux_2_28_x86_64:latest

# System libs for BLAS/LaTeX tooling
RUN yum -y install openblas openblas-devel lapack lapack-devel \
    git which && yum clean all

# Python venv inside container
ENV VENV=/opt/venv
RUN /opt/python/cp311-cp311/bin/python -m venv $VENV
ENV PATH="$VENV/bin:$PATH"

WORKDIR /work
COPY requirements.txt /work/
RUN python -m pip install -U pip wheel && \
    python -m pip install -r requirements.txt

# Default workdir
CMD ["bash"]
