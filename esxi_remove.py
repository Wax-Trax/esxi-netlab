#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This module removes the ESXi lab configuration from the server.
"""
import time
from paramiko import SSHClient, AutoAddPolicy


def esxi_remove(**kwargs):

    lab = kwargs["lab"]
    esxi = kwargs["esxi"]
    esxi_pass = kwargs["esxi_pass"]

    esxi_host = lab["lab_options"]["term_serv"]
    esxi_username = lab["lab_options"]["esxi_username"]
    labname = lab["lab_options"]["lab_name"]

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=esxi_host, username=esxi_username, password=esxi_pass)

    # Discover ESXi Lab VMIDs based on hostname
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
        if vm[1] in hostnames:  # Include only VMs from the lab
            vmids.append((vmid, vm_name, vmx))

    # Double-check before actually deleting :-)
    print("\n")
    for vm in vmids:
        print(f"{vm[0]}: {vm[2]}")
    proceed = input("\nThe above VMs will deleted. Do you wish to "
                    "proceed? (y/n): ")
    if proceed.lower() == "y":  # Anything else will cancel lab removal
        # Power off lab VMs
        print("\n--> Powering off lab VMs:")
        for vm in vmids:
            stdin, stdout, stderr = ssh.exec_command(
                f"vim-cmd vmsvc/power.off {vm[0]}")
            time.sleep(0.5)
            stdin.close()
            stdout.close()
            stderr.close()
        time.sleep(5)

         # Unregister lab VMs
        print("\n--> Unregistering lab VMs:")
        for vm in vmids:
            stdin, stdout, stderr = ssh.exec_command(
                f"vim-cmd vmsvc/unregister {vm[0]}")
            time.sleep(0.5)
            stdin.close()
            stdout.close()
            stderr.close()

        # Delete lab VMs
        print("\n--> Deleting lab VMs:")
        for vm in esxi["remove_vms"]:
            stdin, stdout, stderr = ssh.exec_command(vm)
            time.sleep(0.5)
            stdin.close()
            stdout.close()
            stderr.close()

        # Remove lab portgroups
        print("\n--> Deleting lab port groups:")
        for pg in esxi["portgroup_remove"]:
            stdin, stdout, stderr = ssh.exec_command(pg)
            time.sleep(0.2)
            stdin.close()
            stdout.close()
            stderr.close()

        ssh.close()

        print("\n\n--> Lab has been removed from ESXi server\n\n")
