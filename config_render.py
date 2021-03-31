#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module renders the configuration from Jinja2 template.
"""
from jinja2 import Environment, FileSystemLoader
from netaddr import IPNetwork as ipnet

j2_env = Environment(loader=FileSystemLoader("."))


def render(**kwargs):

    lab = kwargs["lab"]
    interfaces = kwargs["interfaces"]
    j2_file = kwargs["j2_file"]
    output = kwargs["output"]

    # J2 file passed in from command-line
    template = j2_env.get_template(j2_file)

    # Dict to hold configs to pass on to deployment with node ID as key
    rendered_configs = {}

    # Generate the set of nodes from the interface list
    nodes = sorted(set([int(node[0]) for node in interfaces]))

    # Convert IOS/XE/FreeRTR IPv4 addresses to mask format with netaddr library
    for iface in interfaces:
        if "ios" in lab["nodes"][int(iface[0])]["platform"] or \
                "freertr" in lab["nodes"][int(iface[0])]["platform"]:
            ipaddr = ipnet(iface[3])
            ip = str(ipaddr.ip)
            mask = str(ipaddr.netmask)
            iface[3] = f"{ip} {mask}"

        # FreeRTR puts a space between IPv6 and /
        if "freertr" in lab["nodes"][int(iface[0])]["platform"]:
            ipv6 = iface[4].split("/")
            iface[4] = f"{ipv6[0]} /{ipv6[1]}"

    for node in nodes:
        node_interfaces = [iface for iface in interfaces
                           if iface[0] == node]

        render = template.render(lab=lab, node=node, ifaces=node_interfaces)

        rendered_configs[node] = render

        # Create configuration text files if output flag specified
        if output:
            outfile = f'output/{lab["lab_options"]["lab_name"]}__' \
                      f'{lab["nodes"][node]["hostname"]}.txt'
            with open(outfile, "w") as f:
                f.write(render)

    return rendered_configs
