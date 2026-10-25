# Dockerfile: Standardized DHCP Relay image with auto-startup
# Logic Name: dhcp-lab.dhcprelay:latest
# Base: labtainers/labtainer.network.ssh2 (Ubuntu 20.04 Focal)
FROM labtainers/labtainer.network.ssh2:latest
LABEL version=3
LABEL base=labtainers/labtainer.network.ssh2.5a46b1ccd9e9
ENV DEBIAN_FRONTEND=noninteractive

# Install ISC DHCP Relay, iptables, routing and diagnostic tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        isc-dhcp-relay \
        tcpdump \
        iputils-ping \
        net-tools \
        iptables \
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

# Setup systemd service to auto-enable ip_forward and start dhcrelay on boot
RUN printf '[Unit]\nDescription=DHCP Relay Auto-Configuration and Startup\nAfter=network.target\n\n[Service]\nType=oneshot\nExecStart=/bin/bash -c "sysctl -w net.ipv4.ip_forward=1; /usr/sbin/dhcrelay -4 -i eth0 -i eth1 192.168.0.100 2>/dev/null || true"\nRemainAfterExit=yes\n\n[Install]\nWantedBy=multi-user.target\n' > /etc/systemd/system/dhcp-relay-init.service && \
    systemctl enable dhcp-relay-init.service

# Container init uses root for systemd
USER root
