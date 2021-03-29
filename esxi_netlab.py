#!/usr/bin/env python
"""
Author: Jedadiah Casey, @Wax_Trax, neckercube.com
This script generates and instantiates a networking lab on an ESXi server
"""
import argparse
from getpass import getpass

import config_deploy
import config_render
import esxi_create
import esxi_deploy
import esxi_remove
import ip_generate
import iterm2_profile
import validate_nodes

# Required file describing the base platform ESXi VMs
NODE_DEFS = "platform_definitions.yaml"


def main(options):

    # Determines whether or not to generate output configuration files
    output = vars(options)['output']

    # Determines whether or not the ESXi lab infrastructure will be pushed
    deploy = vars(options)['esxi_deploy']

    # Determines whether or not to power on VMs after creation
    power = vars(options)['power']

    # Required YAML file for lab passed as command-line argument
    node_file = vars(options)['node_file']

    # Jinja2 file for the lab node configurations
    j2_file = vars(options)['node_config']

    # Ensure base node definitions are valid
    validated_platforms = validate_nodes.validate_platform_defs(NODE_DEFS)

    # Ensure lab node definitions are valid
    lab = validate_nodes.validate_lab_defs(node_file, validated_platforms)

    # Generate iTerm2 dynamic profile
    if vars(options)['iterm2']:
        iterm2_profile.profile_gen(lab)

    # Generate ESXI configuration
    if vars(options)['esxi_create']:
        esxi_gen(lab, validated_platforms, output, deploy)

    # Get ESXi host SSH password if deploying or removing lab configuration
    if deploy or vars(options)['esxi_remove']:
        esxi_pass = getpass("Please enter ESXi host password for username "
                            f'"{lab["lab_options"]["esxi_username"]}": ')

    # ESXi deploy
    if deploy:
        esxi = esxi_gen(lab, validated_platforms, output, deploy)
        esxi_dep(lab, esxi, power, output, esxi_pass)

    # ESXi remove
    if vars(options)['esxi_remove']:
        esxi = esxi_gen(lab, validated_platforms, output, deploy)
        esxi_rem(lab, esxi, esxi_pass)

    # Generate IP addresses for loopbacks and neighbor interconnections
    if vars(options)['ipgen']:
        esxi = esxi_gen(lab, validated_platforms, output, deploy)
        ip_gen(lab, validated_platforms, esxi, output)

    # Generate node configurations from specified Jinja2 template
    if vars(options)['node_config']:
        esxi = esxi_gen(lab, validated_platforms, output, deploy)
        interfaces = ip_gen(lab, validated_platforms, esxi, output)
        render = lab_render(lab, interfaces, j2_file, output)

        # Push device configurations via telnet serial console
        if vars(options)['push_config']:
            input(
                "\n\n--> Please ensure all lab VMs are ready for configuration "
                "before proceeding. Press enter to continue.")

            config_deploy.config_threads(lab, render)


def esxi_gen(lab, validated_platforms, output, deploy):
    # Create individual node configurations
    esxigen = esxi_create.esxi_create(lab=lab,
                                      platforms=validated_platforms,
                                      deploy=deploy,
                                      output=output,
                                      )
    return esxigen


def esxi_dep(lab, esxi, power, output, esxi_pass):
    # Create individual node configurations
    vmids = esxi_deploy.esxi_deploy(lab=lab,
                                    esxi=esxi,
                                    power=power,
                                    output=output,
                                    esxi_pass=esxi_pass,
                                    )
    return vmids


def esxi_rem(lab, esxi, esxi_pass):
    # Remove ESXi lab configuration
    esxi_remove.esxi_remove(lab=lab, esxi=esxi, esxi_pass=esxi_pass)


def ip_gen(lab, validated_platforms, esxi, output):
    ip = ip_generate.lab_ip_gen(lab=lab,
                                platforms=validated_platforms,
                                esxi_interfaces=esxi["neighbor_interfaces"],
                                output=output,
                                )
    return ip


def lab_render(lab, interfaces, j2_file, output):
    render = config_render.render(lab=lab,
                                  interfaces=interfaces,
                                  j2_file=j2_file,
                                  output=output,
                                  )
    return render


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ESXi network lab "
                                                 "configuration and deployment")

    parser.add_argument("-n",
                        "--node-file",
                        action="store",
                        type=str,
                        required=True,
                        help="YAML file containing your lab nodes (REQUIRED)",
                        metavar="node_file.yaml",
                        dest="node_file")

    parser.add_argument("-o",
                        "--output-files",
                        action="store_true",
                        help="Save all configuration output to files",
                        dest="output")

    parser.add_argument("-ec",
                        "--esxi-create",
                        action="store_true",
                        help="Generate ESXi lab configuration script file only "
                             "(no deployment)",
                        dest="esxi_create")

    parser.add_argument("-ed",
                        "--esxi-deploy",
                        action="store_true",
                        help="Generate and deploy ESXi lab configuration "
                             "to server",
                        dest="esxi_deploy")

    parser.add_argument("-er",
                        "--esxi-remove",
                        action="store_true",
                        help="Remove ESXi lab configuration from server",
                        dest="esxi_remove")

    parser.add_argument("-p",
                        "--power-on-lab",
                        action="store_true",
                        help="Power on lab VMs after deployment (requires -ed)",
                        dest="power")

    parser.add_argument("-it",
                        "--iterm2",
                        action="store_true",
                        help="Generate a dynamic profile for iTerm2 on macOS",
                        dest="iterm2")

    parser.add_argument("-ip",
                        "--generate-ip",
                        action="store_true",
                        help="Generate IP addresses for loopbacks and "
                             "neighbor interfaces from your lab file",
                        dest="ipgen")

    parser.add_argument("-nc",
                        "--node-configs",
                        action="store",
                        type=str,
                        help="Generate lab device configurations from the "
                             "specified Jinja2 file (implies -ip)",
                        metavar="lab-config.j2",
                        dest="node_config")

    parser.add_argument("-pc",
                        "--push-node-configs",
                        action="store_true",
                        help="Push generated lab device configurations "
                             "(requires -nc and assumes the ESXi "
                             "portion (-ed) has been fully deployed "
                             "and booted)",
                        dest="push_config")

    args = parser.parse_args()

    main(args)
