#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module verifies that the nodes defined in the specified YAML files conform
  to the environment constraints. This module is designed to crash with
  specific error messages when certain potentially common mistakes happen.
"""
from yaml import safe_load


# Validate the platform definitions YAML file
def validate_platform_defs(yaml_file):

    # Can we load the file?
    try:
        with open(yaml_file) as f:
            nodes = safe_load(f)
    except:
        raise ValueError(f"Unable to load file \"{yaml_file}\"")

    for node in nodes:

        # Folder tests
        try:
            if not nodes[node]["folder"]:
                raise ValueError(f"Folder name for platform \"{node}\" "
                                 f"not defined")
        except:
            raise ValueError("Missing or malformed folder name for platform: "
                             f"\"{node}\"")

        if " " in nodes[node]["folder"]:
            raise ValueError("Folder name cannot contain spaces for platform: "
                             f"\"{node}\"")

        # Base telnet port tests
        try:
            if not nodes[node]["base_tport"]:
                raise ValueError(f"base_tport missing for platform \"{node}\"")
            base_tport = int(nodes[node]["base_tport"])
        except:
            raise ValueError("Missing or malformed base_tport for platform: "
                             f"\"{node}\"")

        if base_tport < 1025 or base_tport > 65534:
            raise ValueError(f"base_tport for platform \"{node}\" must be "
                             "within 1025 - 65534")

        # Interface count tests, ESXi does not support more than 10 vNICs
        try:
            iface_num = len(nodes[node]["interfaces"])
        except:
            raise ValueError("Missing or malformed interfaces for platform: "
                           f"\"{node}\"")

        if iface_num > 10:
            raise ValueError(f"Too many interfaces for platform: \"{node}\" "
                           f"({iface_num} counted, maximum 10)")

    return nodes  # All platforms should be successfully-validated now


# Validate the specified lab node YAML file
def validate_lab_defs(yaml_file, platforms):

    # Can we load the file?
    try:
        with open(yaml_file) as f:
            lab = safe_load(f)
    except:
        raise ValueError(f"Unable to load file \"{yaml_file}\"")

    # Lab name tests
    try:
        if not lab["lab_options"]["lab_name"]:
            raise ValueError(f"Lab option lab_name not defined")
    except:
        raise ValueError("Missing or malformed lab option: lab_name")

    if " " in lab["lab_options"]["lab_name"]:
        raise ValueError("Lab option lab_name cannot contain spaces")

    # ESXi host tests
    try:
        if not lab["lab_options"]["term_serv"]:
            raise ValueError(f"Lab option term_serv not defined")
    except:
        raise ValueError("Missing or malformed lab option: term_serv")

    if " " in lab["lab_options"]["term_serv"]:
        raise ValueError("Lab option term_serv cannot contain spaces")

    # ESXi username tests
    try:
        if not lab["lab_options"]["esxi_username"]:
            raise ValueError(f"Lab option esxi_username not defined")
    except:
        raise ValueError("Missing or malformed lab option: esxi_username")

    if " " in lab["lab_options"]["esxi_username"]:
        raise ValueError("Lab option esxi_username cannot contain spaces")

    # Is the base telnet port within the range 20 - 65?
    try:
        if not lab["lab_options"]["tport_base"]:
            raise ValueError(f"Lab option tport_base not defined")
        tpb = int(lab["lab_options"]["tport_base"])
        if tpb < 20 or tpb > 65:
            raise ValueError(f"Lab tport_base must be between 20 - 65. "
                             f"As configured: \"{tpb}\"")
    except:
        raise ValueError(f"Lab tport_base must be between 20 - 65.")

    # ESXi datastore tests
    try:
        if not lab["lab_options"]["datastore"]:
            raise ValueError(f"Lab option datastore not defined")
    except:
        raise ValueError("Missing or malformed lab option: datastore")

    if " " in lab["lab_options"]["datastore"]:
        raise ValueError("Lab option datastore cannot contain spaces")

    # ESXi vSwitch tests
    try:
        if not lab["lab_options"]["vswitch"]:
            raise ValueError(f"Lab option vswitch not defined")
    except:
        raise ValueError("Missing or malformed lab option: vswitch")

    if " " in lab["lab_options"]["vswitch"]:
        raise ValueError("Lab option vswitch cannot contain spaces")

    # ESXi base Port Group tests
    try:
        if not lab["lab_options"]["pg_base"]:
            raise ValueError(f"Lab option pg_base not defined")
    except:
        raise ValueError("Missing or malformed lab option: pg_base")

    if " " in lab["lab_options"]["pg_base"]:
        raise ValueError("Lab option pg_base cannot contain spaces")

    # Evaluate the individual lab nodes
    for node in lab["nodes"]:

        # Ensure node number is an int between 1 - 254
        try:
            if int(node) < 1 or int(node) > 254:
                raise ValueError(f"All nodes must be defined as a number "
                                 f"between 1 - 254. Node: \"{node}\"")
        except:
            raise ValueError(f"All nodes must be defined as a number "
                             f"between 1 - 254. Node: \"{node}\"")

        # Hostname tests
        try:
            if not lab["nodes"][node]["hostname"]:
                raise ValueError(f"Hostname not defined for node: \"{node}\"")
        except:
            raise ValueError("Missing or malformed hostname for node: "
                           f"\"{node}\"")

        if " " in lab["nodes"][node]["hostname"]:
            raise ValueError("Hostname cannot contain spaces for node: "
                           f"\"{node}\"")

        # Check for duplicate hostnames (duplicates cause issues elsewhere)
        for node2 in lab["nodes"]:
            hostname1 = lab["nodes"][node]["hostname"]
            hostname2 = lab["nodes"][node2]["hostname"]
            if node != node2:
                if hostname1 == hostname2:
                    raise ValueError("Duplicate hostname detected for node "
                                     f"\"{node}\" and node \"{node2}\"")

        # Platform tests
        try:
            if not lab["nodes"][node]["platform"]:
                raise ValueError(f"Platform not specified for node: \"{node}\"")
        except:
            raise ValueError("Missing or malformed platform for node: "
                           f"\"{node}\"")

        if lab["nodes"][node]["platform"] not in platforms:
            raise ValueError(f"Base platform \""
                             f"{lab['nodes'][node]['platform']}\" "
                             f"not in available platform definitions for node: "
                             f"\"{node}\"")

        # Ensure Site number is an int between 1 - 254
        try:
            if not lab["nodes"][node]["site"]:
                raise ValueError(f"Site number (1 - 254) not defined for "
                                 f"node: \"{node}\"")
            if int(lab["nodes"][node]["site"]) < 1 or \
               int(lab["nodes"][node]["site"]) > 254:
                raise ValueError(f"Sites must be defined as a number "
                                 f"between 1 - 254. Node: \"{node}\"")
        except:
            raise ValueError(f"Sites must be defined as a number "
                             f"between 1 - 254. Node: \"{node}\"")

        # Determine number of interfaces for platform (for neighbor check)
        iface_count = 0
        for iface in platforms[lab["nodes"][node]["platform"]]["interfaces"]:
            if platforms[lab["nodes"][node]["platform"]]["interfaces"][iface]:
                iface_count += 1

        # Neighbors check
        # Warn if no neighbors but continue because it might be on purpose
        neighbors_defined = True
        try:
            if not lab["nodes"][node]["neighbors"]:
                print(f"No neighbors defined for node: \"{node}\"")
                neighbors_defined = False
        except:
            print(f"No neighbors defined for node: \"{node}\"")
            neighbors_defined = False

        if neighbors_defined:
            # Check if the node has more neighbors than interfaces
            num_neighbors = len(lab["nodes"][node]["neighbors"])
            if num_neighbors > iface_count:
                raise ValueError(f"Node \"{node}\" has {num_neighbors} "
                                 f"neighbors assigned but only "
                                 f"{iface_count} total available interfaces")

            for neighbor in lab["nodes"][node]["neighbors"]:
                # Check if neighbored with self
                if neighbor is node:
                    raise ValueError(f"Node cannot be neighbor with "
                                     f"itself for node: \"{node}\"")

                # Check that all defined neighbors exist
                if neighbor not in lab["nodes"]:
                    raise ValueError(f"Neighbor \"{neighbor}\" does not exist "
                                     f"in lab for node: \"{node}\"")

                # Check for reciprocal connection in neighbor
                if node not in lab["nodes"][neighbor]["neighbors"]:
                    raise ValueError(f"Node: \"{node}\" has neighbor "
                                     f"\"{neighbor}\" defined, but the "
                                     f"neighbor \"{neighbor}\" does not have "
                                     f"\"{node}\" listed as one of its "
                                     f"neighbors")

                # Check for reciprocal multi-connections in neighbor
                xcount = lab["nodes"][node]["neighbors"].count(neighbor)
                ycount = lab["nodes"][neighbor]["neighbors"].count(node)
                if xcount != ycount:
                    raise ValueError(f"Node \"{node}\" has \"{xcount}\" "
                                     f"connection(s) to neighbor \"{neighbor}\""
                                     f" defined, but \"{neighbor}\" has "
                                     f"\"{ycount}\" connction(s) defined. "
                                     f"These values must match.")

    return lab
