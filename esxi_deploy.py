#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module uses the output from esxi_create.py to push the commands
 to the ESXi server via SSH session.
"""
import time
from paramiko import SSHClient, AutoAddPolicy


def esxi_deploy(**kwargs):

    lab = kwargs["lab"]
    esxi = kwargs["esxi"]
    power = kwargs["power"]
    output = kwargs["output"]
    esxi_pass = kwargs["esxi_pass"]

    esxi_host = lab["lab_options"]["term_serv"]
    esxi_username = lab["lab_options"]["esxi_username"]
    datastore = lab['lab_options']['datastore']
    labname = lab["lab_options"]["lab_name"]

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=esxi_host, username=esxi_username, password=esxi_pass)

    esxi_vmid = []

    print("\n--> Creating VMs:")
    for vm in esxi["clone_vms"]:
        print(vm, end=" ")  # puts following status on the same line
        stdin, stdout, stderr = ssh.exec_command(f"cd /vmfs/volumes/"
                                                 f"{datastore} && {vm}")
        time.sleep(0.2)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("--> VM created")
        else:
            print("--> Error: Unable to clone, or folder already exists")
            # The script will continue if the VM folder already exists

        stdin.close()
        stdout.close()
        stderr.close()

    print("\n--> Creating Port Groups:")
    for pg in esxi["portgroup_create"]:
        print(pg)
        stdin, stdout, stderr = ssh.exec_command(pg)
        time.sleep(0.2)
        stdin.close()
        stdout.close()
        stderr.close()

    print("\n--> Assigning Telnet Console Ports:")
    for port in esxi["telnet_ports"]:
        print(port)
        stdin, stdout, stderr = ssh.exec_command(port)
        time.sleep(0.2)
        stdin.close()
        stdout.close()
        stderr.close()

    print("\n--> Assigning Port Groups to vNICs:")
    for vnic in esxi["interface_portgroups"]:
        print(vnic)
        stdin, stdout, stderr = ssh.exec_command(vnic)
        time.sleep(0.2)
        stdin.close()
        stdout.close()
        stderr.close()

    print(f"\n--> Registering VMs on {esxi_host}:")
    for reg in esxi["register_vms"]:
        print(reg, end=" ")
        stdin, stdout, stderr = ssh.exec_command(reg)
        time.sleep(0.2)
        lines = stdout.readlines()
        vmid = lines[-1].strip("\n")
        if vmid == "}":
            print("  --> VM was previously registered")
        else:
            print(f"--> VMID: {vmid}")
        esxi_vmid.append(vmid)
        stdin.close()
        stdout.close()
        stderr.close()

    # Discover ESXi Lab VMIDs using the lab VM hostnames
    stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/getallvms")
    lines = stdout.readlines()
    stdin.close()
    stdout.close()
    stderr.close()

    hostnames = []
    for node in lab["nodes"]:
        hostnames.append(f'{labname}_{lab["nodes"][node]["hostname"]}')

    vmids = []
    for line in lines:
        vm = line.split()
        vmid = vm[0]  # '156'
        vm_name = vm[1]  # 'Lab_HOSTNAME'
        vmx = vm[3]  # 'Lab_HOSTNAME/XRv-6.3.1.vmx'
        if vm[1] in hostnames:  # Only add VMs belonging to the lab
            vmids.append((vmid, vm_name, vmx))

    print("\n\n--> ESXi VM configuration complete.\n\n")

    if power:
        print(f"\n--> Powering on VMs:")

        for vm in vmids:  # ('42', 'Lab_ASBR_1B', 'Lab_ASBR_1B/XE-17.3.1a.vmx')
            print(f"vim-cmd vmsvc/power.on {vm[0]} --> Node {vm[1]}")
            stdin, stdout, stderr = ssh.exec_command(
                f"vim-cmd vmsvc/power.on {vm[0]}")
            time.sleep(0.2)
            stdin.close()
            stdout.close()
            stderr.close()

    ssh.close()

    # Add the VMIDs to the output file (if specified) for post-lab cleanup
    if output:
        outfile = f'output/{lab["lab_options"]["lab_name"]}__ESXi_config.txt'

        with open(outfile, "a") as f:
            f.write('\n--> UNREGISTER Lab VMs:\n')
            for vm in vmids:
                f.write(f"vim-cmd vmsvc/unregister {vm[0]}\n")

    return vmids
