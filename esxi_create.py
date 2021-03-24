#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module generates the ESXi configuration commands.
"""


def esxi_create(**kwargs):

    lab = kwargs["lab"]
    platforms = kwargs["platforms"]
    output = kwargs["output"]
    deploy = kwargs["deploy"]
    labname = lab["lab_options"]["lab_name"]

    # Generate list of neighbor interconnections
    links = []
    neighbor_interfaces = {}
    for node in lab["nodes"]:

        neighbor_interfaces[node] = []

        # Determine available interfaces for the node platform
        platform = lab["nodes"][node]["platform"]

        ifaces = []
        for iface in platforms[platform]["interfaces"]:
            # Account for "None" interfaces such as XRv management interfaces
            if platforms[platform]["interfaces"][iface]:
                ifaces.append(iface)

        # Assign interface ID to each neighbor
        for neighbor in lab["nodes"][node]["neighbors"]:
            # Reference links between two neighbors by hostname
            node_name = lab["nodes"][node]["hostname"]
            neighbor_name = lab["nodes"][neighbor]["hostname"]
            links.append([node_name, neighbor_name])

            # Interface ID for each neighbor connection
            neighbor_interfaces[node].append((neighbor, ifaces.pop(0)))

    # Account for multiple links between neighbors (add xNUM to name)
    multilinks = []
    for index, value in enumerate(links):
        total = links.count(value)
        counter = links[:index].count(value)
        multilinks.append([value[0] + f"_x{(counter + 1)}", value[1] +
                          f"_x{(counter + 1)}"] if total > 1 else value)
    links = multilinks

    # Remove duplicate links (only need A->B, not A->B and B->A)
    links = sorted(list(set(tuple(sorted(link)) for link in links)))

    # Generate list of esxcli commands to add/remove portgroups
    portgroup_create = []  # Commands to create ESXi portgroups
    portgroup_remove = []  # Commands to remove ESXi portgroups

    vswitch = lab["lab_options"]["vswitch"]

    for link in links:
        portgroup_create.append("esxcli network vswitch standard "
                                         f"portgroup add -v {vswitch} "
                                         f"-p {labname}_{link[0]}---{link[1]}")
        portgroup_remove.append("esxcli network vswitch standard "
                                         f"portgroup remove -v {vswitch} "
                                         f"-p {labname}_{link[0]}---{link[1]}")

    # Generate list of commands to create/remove cloned VMs
    clone_vms = []  # Commands to copy base VMs
    remove_vms = []  # Commands to remove copied VMs
    telnet_ports = []  # Commands to set VM serial console telnet port
    interface_portgroups = []  # Commands to set VM vNIC portgroups
    register_vms = []  # Commands to register new VMs into ESXi inventory

    pg_base = lab["lab_options"]["pg_base"]
    datastore = lab['lab_options']['datastore']

    temp_links = links + links  # One PG for each side of the connection

    for node in lab["nodes"]:
        platform = platforms[lab["nodes"][node]["platform"]]["folder"]
        hostname = lab["nodes"][node]["hostname"]
        platform_port = platforms[lab["nodes"][node]["platform"]]["base_tport"]
        node_tport = str(lab["lab_options"]["tport_base"] * 1000 + node)
        vm_location = f"/vmfs/volumes/{datastore}/{labname}_{hostname}"

        clone_vms.append(f"sh esxi_thinclone.sh {platform} "
                         f"{labname}_{hostname}")
        remove_vms.append(f"rm -rf {vm_location}")
        telnet_ports.append(f"sed -i 's/:{platform_port}/:{node_tport}/' "
                            f"{vm_location}/{platform}.vmx")

        for iface in neighbor_interfaces[node]:
            iface_id = iface[1]
            neighbor_hostname = lab["nodes"][iface[0]]["hostname"]

            for link in temp_links:
                if (hostname in link[0] or hostname in link[1]) and \
                   (neighbor_hostname in link[0] or
                    neighbor_hostname in link[1]):
                    group = temp_links.pop(temp_links.index(link))
                    pg = f"{labname}_{group[0]}---{group[1]}"
                    break  # Only need the first match since it is popped

            vnic = (f"sed -i 's/ethernet{iface_id}.networkName = "
                    f"\"{pg_base}\"/ethernet{iface_id}.networkName = "
                    f"\"{pg}\"/' {vm_location}/{platform}.vmx")

            interface_portgroups.append(vnic)

        register_vms.append(f"vim-cmd solo/registervm "
                            f"{vm_location}/{platform}.vmx")

    # Create a text file with all these commands if output specified
    if output:
        outfile = f'output/{lab["lab_options"]["lab_name"]}__ESXi_config.txt'

        with open(outfile, "w") as f:
            f.write("===== ESXi Lab Configuration script: =====\n")

            f.write("\n--> Create ESXi Lab vSwitch Port Groups:\n")
            for row in portgroup_create:
                f.write(f"{row}\n")

            f.write("\n--> Create ESXi Lab VMs:\n")
            f.write(f"cd /vmfs/volumes/{datastore}\n")
            for row in clone_vms:
                f.write(f"{row}\n")

            f.write("\n--> Set ESXi Lab VM Telnet Console Ports:\n")
            for row in telnet_ports:
                f.write(f"{row}\n")

            f.write("\n--> Set ESXi Lab VM vNIC Port Groups:\n")
            for row in interface_portgroups:
                f.write(f"{row}\n")

            f.write("\n--> Register Lab VMs in ESXi Inventory:\n")
            for row in register_vms:
                f.write(f"{row}\n")

            f.write("\n\n\n===== ESXi Post-Lab Cleanup: =====\n")

            f.write("\nIMPORTANT: Ensure lab VMs are powered off before "
                    "proceeding\n")

            f.write("\n--> DELETE ESXi Lab VM Directories:\n")
            for row in remove_vms:
                f.write(f"{row}\n")

            f.write("\n--> DELETE ESXi Lab vSwitch Port Groups:\n")
            for row in portgroup_remove:
                f.write(f"{row}\n")

            # Add this message to the file if the lab is not being deployed
            #  with the -ed flag. If the -ed flag is used, the actual VMIDs
            #  will be added to this file when the VMs are registered.
            if not deploy:
                f.write('\n--> UNREGISTER Lab VMs:\n')
                f.write('NOTE: If the --esxi-deploy option was not selected, '
                        'the ESXi VMIDs will be \nunavailable. SSH to the '
                        'server and issue the command '
                        '"vim-cmd vmsvc/getallvms", \nthen run the command'
                        '"vim-cmd vmsvc/unregister VMID"\n\n')

    # Collect the commands to be used for deployment with the -ed flag
    esxi_commands = {
        "portgroup_create": portgroup_create,
        "portgroup_remove": portgroup_remove,
        "clone_vms": clone_vms,
        "remove_vms": remove_vms,
        "telnet_ports": telnet_ports,
        "interface_portgroups": interface_portgroups,
        "register_vms": register_vms,
        "neighbor_interfaces": neighbor_interfaces,
    }

    return esxi_commands
