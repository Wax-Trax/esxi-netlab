#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
- This module pushes the generated configurations to the lab nodes.
- Make sure you lab nodes are fully-booted and ready to accept input!
- You have the option of configuring devices indvidually or simultaneously
- This script currently works with IOS/XE and IOS-XR. You will need to
   create additional platform stanzas to use other platforms.
"""
import time
from telnetlib import Telnet
from threading import Thread


def push_configs(node, lab, render, display):

    esxi_host = lab["lab_options"]["term_serv"]
    tport = lab["lab_options"]["tport_base"] * 1000 + node
    platform = lab["nodes"][node]["platform"]

    conn = Telnet()
    conn.set_debuglevel(display)
    conn.open(host=esxi_host, port=tport, timeout=3)

    # IOS/XE/XR-specific configuration
    if "ios" in platform or "xrv" in platform or "freertr" in platform:

        # Account for IOS/XE unconfigured state
        if "ios" in platform:
            conn.write(b"\r")
            time.sleep(3)
            unconf = conn.read_until(b"[yes/no]:", timeout=3)
            if b"[yes/no]:" in unconf:
                conn.write("no".encode("ascii") + b"\r")
                time.sleep(1)
                conn.read_until("passed code signing verification", timeout=600)
                conn.write(b"\r")
                time.sleep(1)
            conn.write(b"\r")
            time.sleep(0.3)
            conn.write("enable".encode("ascii") + b"\r")
            time.sleep(0.3)

        # Account for XRv unconfigured state
        if "xrv" in platform:
            conn.write(b"\r")
            unconf = conn.read_until(b"Enter root-system username:", timeout=3)
            if b"root-system username" in unconf:
                conn.write("xrv".encode("ascii") + b"\r")
                time.sleep(3)
                conn.write("xrvadmin".encode("ascii") + b"\r")
                time.sleep(3)
                conn.write("xrvadmin".encode("ascii") + b"\r")
                time.sleep(3)
            time.sleep(1)
            conn.write("xrv".encode("ascii") + b"\r")
            time.sleep(1)
            conn.write("xrvadmin".encode("ascii") + b"\r")
            time.sleep(1)

        conn.write(b"\r")
        conn.write("term len 0".encode("ascii") + b"\r")
        time.sleep(0.3)
        conn.write("conf t".encode("ascii") + b"\r")
        time.sleep(0.3)
        for line in render[node].split("\n"):
            conn.write(line.encode("ascii") + b"\r")
            time.sleep(0.2)
        if "xrv" in platform:
            conn.write("commit".encode("ascii") + b"\r")
            time.sleep(1)
            conn.write("exit".encode("ascii") + b"\r")
            time.sleep(0.3)
        conn.write("exit".encode("ascii") + b"\r")
        time.sleep(0.3)
        if "ios" in platform or "freertr" in platform:
            conn.write("wr".encode("ascii") + b"\r")
            time.sleep(10)  # Time needed for IOSv writing to GRUB
            conn.write("exit".encode("ascii") + b"\r")
        conn.close()

    if "vyos" in platform:
        conn.write(b"\r")
        time.sleep(1)
        conn.write("vyos".encode("ascii") + b"\r")
        time.sleep(1)
        conn.write("vyos".encode("ascii") + b"\r")
        time.sleep(1)

        conn.write(b"\r")
        conn.write("configure".encode("ascii") + b"\r")
        time.sleep(0.5)
        for line in render[node].split("\n"):
            conn.write(line.encode("ascii") + b"\r")
            time.sleep(0.2)
        conn.write("commit".encode("ascii") + b"\r")
        time.sleep(5)
        conn.write("set service lldp interface all".encode("ascii") + b"\r")
        time.sleep(0.3)
        conn.write("commit".encode("ascii") + b"\r")
        time.sleep(5)
        conn.write("save".encode("ascii") + b"\r")
        time.sleep(0.5)
        conn.write("exit".encode("ascii") + b"\r")
        time.sleep(0.3)
        conn.close()

    if "vmx" in platform:
        conn.write(b"\r")
        time.sleep(1)
        conn.write("root".encode("ascii") + b"\r")
        time.sleep(1)
        conn.write("Juniper".encode("ascii") + b"\r")
        time.sleep(1)
        conn.write("cli".encode("ascii") + b"\r")
        time.sleep(1)

        conn.write(b"\r")
        conn.write("configure".encode("ascii") + b"\r")
        time.sleep(0.5)
        for line in render[node].split("\n"):
            conn.write(line.encode("ascii") + b"\r")
            time.sleep(0.2)
        conn.write("set protocols lldp interface all".encode("ascii") + b"\r")
        time.sleep(0.3)
        conn.write("commit".encode("ascii") + b"\r")
        time.sleep(5)
        conn.write("save config.cfg".encode("ascii") + b"\r")
        time.sleep(0.5)
        conn.write("exit".encode("ascii") + b"\r")
        time.sleep(0.3)
        conn.close()

    # Other platform-specifics will go below here
    # if "PLATFORM" in platform:

    print(f"Configuration to node {node} sent.")


def config_threads(lab, render):

    multi_threading = input("\n--> Push commands to all devices "
                            "simultaneously? (y/n): ")
    if multi_threading.lower() == "y":
        multi_threading = True
    else:
        multi_threading = False

    display = input("\n--> Display configuration progress? (y/n): ")
    if display.lower() == "y":
        display = True
    else:
        display = False

    for node in render:
        print(f"Configuring: {node}")
        if multi_threading is True:
            threads = Thread(target=push_configs,
                             args=(node, lab, render, display))
            threads.start()
        else:
            push_configs(node, lab, render, display)
