#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module generates an iTerm2 dynamic profile based on the telnet
  serial console port. The generated file is placed into the user's iTerm2
  preferences folder.
"""
from jinja2 import Environment, FileSystemLoader
from os import path
from uuid import uuid4

ITERM2_TEMPLATE = "iterm2.j2"
ITERM2 = "Library/Application Support/iTerm2/DynamicProfiles"

j2_env = Environment(loader=FileSystemLoader("."))
template = j2_env.get_template(ITERM2_TEMPLATE)


def profile_gen(lab):

    print("\n===== Generating iTerm2 dynamic profile =====\n")

    # iTerm2 supports multiple dynamic profiles. This input is to determine if
    #  you want all nodes to appear under a single lab (so you can open all
    #  nodes from the lab at the same time), or sorted by site.

    site_sort_input = False
    while not site_sort_input:
        site_sort = input("Group by site (S) or by entire lab (L)?: ")
        if site_sort.lower() == "s" or site_sort.lower() == "l":
            site_sort_input = True

    # Generate node information to be used with the template
    tport_base = lab["lab_options"]["tport_base"] * 1000
    iterm_nodes = []
    for node in lab["nodes"]:
        uuid = uuid4()  # Required for iTerm2 dynamic profile
        iterm_nodes.append((lab["nodes"][node]["hostname"],
                            tport_base + node,
                            uuid,
                            lab["nodes"][node]["site"]))

    # Create the dynamic profile file and put it in the iTerm2 folder
    render = template.render(nodes=sorted(iterm_nodes),
                             lab_name=lab["lab_options"]["lab_name"],
                             term_serv=lab["lab_options"]["term_serv"],
                             sort=site_sort.lower())
    pfile = f'{path.expanduser("~")}/{ITERM2}/' \
            f'{lab["lab_options"]["lab_name"]}.json'
    with open(pfile, "w") as f:
        f.write(render)
