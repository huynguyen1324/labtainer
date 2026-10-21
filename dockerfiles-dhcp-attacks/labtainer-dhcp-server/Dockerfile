# Dockerfile: Standardized DHCP Server image
# Logic Name: labtainer-dhcp-server:1.0
# Base: labtainers/labtainer.network.ssh2 (Ubuntu 20.04 Focal)
FROM labtainers/labtainer.network.ssh2:latest
ENV DEBIAN_FRONTEND=noninteractive

# Install ISC DHCP Server, dnsmasq, and diagnostic tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        isc-dhcp-server \
        dnsmasq \
        tcpdump \
        iputils-ping \
        net-tools \
        procps \
        iproute2 && \
    rm -rf /var/lib/apt/lists/*

# Setup non-root user ubuntu with passwordless sudo for Labtainers
RUN id -u ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -u 1000 ubuntu && \
    echo "ubuntu:ubuntu" | chpasswd && \
    adduser ubuntu sudo && \
    sed -i '/%sudo[[:space:]]/d' /etc/sudoers && \
    echo "%sudo ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    mkdir -p /home/ubuntu/.local/bin /home/ubuntu/.local/result /home/ubuntu/.local/config /home/ubuntu/.local/zip && \
    touch /home/ubuntu/.local/.email /home/ubuntu/.local/.labname /home/ubuntu/.local/.seed /home/ubuntu/.local/.watermark && \
    mkdir -p /root/.local/bin /root/.local/result /root/.local/config /root/.local/zip && \
    touch /root/.local/.email /root/.local/.labname /root/.local/.seed /root/.local/.watermark && \
    chown -R ubuntu:ubuntu /home/ubuntu

# Copy DHCP base configuration
COPY dhcpd.conf /etc/dhcp/dhcpd.conf

# Container init uses root for systemd
USER root
