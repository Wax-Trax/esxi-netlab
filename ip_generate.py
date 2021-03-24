#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module generates IP addresses for interconnected links.

IP generation:
- Loopback
  - 192.168.site.device/32
  - fd00:site::device/128
- Physical inter-neighbor
  - 10.lower.higher.device/24
  - fd00:lower:higher::device/64

Returns: [node, hostname, interface, ipv4, ipv6]

Change the loopback and multi-link base to a different /16 below. When
multiple links exist between a pair of neighbors, the MULTI_BASE variable
is used for each connection, going from 1 - 254. The script does not
currently support more than 254 multi-links across the entire lab.
"""

LOOPBACK_BASE = "192.168"  # MUST be a /16 without second dot
MULTI_BASE = "172.30"  # MUST be a /16 without second dot, used for multi-links
CSV_HEADER = '"ID","Hostname","Interface","IPv4","IPv6"\n'


def lab_ip_gen(**kwargs):

    lab = kwargs["lab"]
    platforms = kwargs["platforms"]
    esxi_interfaces = kwargs["esxi_interfaces"]
    output = kwargs["output"]

    interfaces = []

    # Loopbacks
    for node in lab["nodes"]:
        ipv4 = f'{LOOPBACK_BASE}.{lab["nodes"][node]["site"]}.{node}/32'
        ipv6 = f'fd00:{lab["nodes"][node]["site"]}::{node}/128'
        hostname = lab["nodes"][node]["hostname"]
        interfaces.append([node, hostname, "lo0", ipv4, ipv6])

    # Physical interfaces
    for node, interface_set in esxi_interfaces.items():
        platform = lab["nodes"][node]["platform"]
        hostname = lab["nodes"][node]["hostname"]

        last_neighbor = 0  # Used to account for multiple interconnections
        multi_xconnect = 0  # Used to account for multiple interconnections

        for iface in interface_set:

            # Get interface name
            interface = platforms[platform]["interfaces"][iface[1]]

            # Enforce lower-numbered node first to be deterministic
            neighbor_set = sorted((node, iface[0]))

            # Account for multiple interconnections
            if iface[0] == last_neighbor:
                ipv4 = f'{MULTI_BASE}.{multi_xconnect}.{node}/24'
                ipv6 = f'fd00:{neighbor_set[0]}:{neighbor_set[1]}:' \
                       f'{multi_xconnect}::{node}/64'
            else:
                ipv4 = f'10.{neighbor_set[0]}.{neighbor_set[1]}.{node}/24'
                ipv6 = f'fd00:{neighbor_set[0]}:{neighbor_set[1]}::{node}/64'

            # Account for multiple interconnections
            last_neighbor = iface[0]
            multi_xconnect += 1
            if multi_xconnect > 254:
                raise ValueError("This script currently does not support "
                                 "more than 254 multi-connections in the lab")

            interfaces.append([node, hostname, interface, ipv4, ipv6])

    # Create a CSV file with the interfaces and IPs if output specified
    if output:
        outfile = f'output/{lab["lab_options"]["lab_name"]}__' \
                  f'IP_Interfaces.csv'
        with open(outfile, "w") as f:
            f.write(CSV_HEADER)
            for row in interfaces:
                f.write(f'"{row[0]}","{row[1]}","{row[2]}","{row[3]}",'
                        f'"{row[4]}"\n')

    return interfaces
