# Dockerfile: Standardized Kali / Attacker image
# Logic Name: labtainer-kali-attacker:1.0
# Base: labtainers/labtainer.network.ssh2 (Ubuntu 20.04 Focal)
FROM labtainers/labtainer.network.ssh2:latest
LABEL version=3
LABEL base=labtainers/labtainer.network.ssh2.5a46b1ccd9e9
ENV DEBIAN_FRONTEND=noninteractive

# Install Yersinia, Scapy, Network diagnostic and attack tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        yersinia \
        dhcpstarv \
        python3-scapy \
        tcpdump \
        tshark \
        iputils-ping \
        net-tools \
        nmap \
        arp-scan \
        isc-dhcp-client \
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

# Setup service to flush static IP at boot so attacker can request dynamic IP
RUN printf '[Unit]\nDescription=Flush initial static IP on external interface\nAfter=network.target\n\n[Service]\nType=oneshot\nExecStart=/bin/bash -c "ip -4 addr flush dev eth0; ip link set eth0 up"\nRemainAfterExit=yes\n\n[Install]\nWantedBy=multi-user.target\n' > /etc/systemd/system/flush-ip.service && \
    systemctl enable flush-ip.service

# Copy DHCP Release Spoofing script into container
COPY dhcp-release-spoofing.py /usr/local/bin/dhcp-release-spoofing.py
RUN chmod +x /usr/local/bin/dhcp-release-spoofing.py

# Container init uses root for systemd
USER root
