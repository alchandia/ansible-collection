FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN \
  apt update && \
  apt install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    openssh-client \
    ca-certificates \
    unzip && \
  apt clean && \
  apt autoremove --purge

RUN \
    mkdir -p /home/ubuntu/.vscode-server/extensions && \
    chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server

USER ubuntu
WORKDIR /workspace/src
ENTRYPOINT ["/bin/bash","-c","sleep infinity"]
