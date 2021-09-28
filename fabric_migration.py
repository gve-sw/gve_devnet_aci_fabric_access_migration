#
# Copyright (c) 2021 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at
#                https://developer.cisco.com/docs/licenses
# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.
#

import requests
import pprint
import json
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
import re

from ACI_create_objects import *

from config import *


def find_values(id, json_repr):
    ''' Helper function to find all values associated with a particular key in a JSON tree including in the subtree.'''
    # Ex: json_repr = '{"P1": "ss", "Id": 1234, "P2": {"P1": "cccc"}, "P3": [{"P1": "aaa"}]}'
    # print(find_values('P1', json_repr))
    # ['cccc', 'aaa', 'ss']
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict) # Return value ignored.
    return results


# Get authentication token for APIC.
# Auth Walkthrough https://blog.wimwauters.com/networkprogrammability/2020-03-19-aci_python_requests/
def get_token():
    '''Function to retrieve the auth token required to authenticate further requests'''

    url = f"{base}/aaaLogin.json"
    payload = {
        "aaaUser": {
            "attributes": {
                "name": user,
                "pwd": password
            }
        }
    }
    headers = {'Content-Type': 'text/plain'}
    requests.packages.urllib3.disable_warnings()
    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    # print(response.json())
    return response.json()['imdata'][0]['aaaLogin']['attributes']['token']


def save_aci_config_snapshot(description="API Generated Snapshot"):
    '''Saves a snapshot of the ACI configuration accessed via the Admin Tab in APIC'''
    token = get_token()
    payload = {
                 "configExportP": {
                        "attributes": {
                            "dn": "uni/fabric/configexp-defaultOneTime",
                            "adminSt": "triggered",
                            "descr": description
                        }
                 }
            }
    url = f'{base}/mo.json'
    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.post(url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        print('Saved ACI Config Snapshot!')
        return response.status_code
    else:
        print('ERROR! Unable to save ACI Snapshot')
        return response.status_code


def get_fabric_nodes():
    '''Gets all Non-Controller nodes (including both leafs and spines)'''

    token = get_token()
    url = f"{base}/node/class/fabricNode.json?query-target-filter=ne(fabricNode.role, %22controller%22)"
    # url = f'{base}/node/class/fabricNode.json?query-target-filter=and(ne(fabricNode.role, %22controller%22), ge(fabricNode.id,%22101%22),le(fabricNode.id,%22202%22))'

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()


def get_fabric_node_by_id(node_id):
    '''Gets a specific node with id equal to the value passed in
    :param node_id: the node_id of the desired node'''
    token = get_token()
    url = f"{base}/node/class/fabricNode.json?query-target-filter=and(ne(fabricNode.role, %22controller%22),eq(fabricNode.id,%22{node_id}%22))"
    # url = f'{base}/node/class/fabricNode.json?query-target-filter=and(ne(fabricNode.role, %22controller%22), ge(fabricNode.id,%22101%22),le(fabricNode.id,%22202%22))'

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()


def get_leaf_switch_profiles():
    token = get_token()

    # Get Leaf Switch Profiles
    url = f"{base}/node/mo/uni/infra.json?query-target=children&target-subtree-class=infraNodeP&query-target-filter" \
          f"=not(wcard(infraNodeP.dn,%22__ui_%22))&rsp-subtree=full&rsp-subtree-class=infraLeafS,infraRsAccPortP," \
          f"infraRsAccCardP,infraNodeBlk,infraRsAccNodePGrp&order-by=infraNodeP.name" #|asc&page=0&page-size=15 "

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()


def get_leaf_interface_profiles():
    token = get_token()

    # Get Leaf Interface Profiles
    url = f'{base}/node/mo/uni/infra.json?query-target=subtree&target-subtree-class=infraAccPortP&query-target-filter' \
          f'=not(wcard(infraAccPortP.dn,"__ui_"))&query-target=children&target-subtree-class=infraAccPortP&rsp' \
          f'-subtree=full&rsp-subtree-class=infraHPortS,infraPortBlk,infraRsAccBaseGrp,' \
          f'infraSubPortBlk&order-by=infraAccPortP.name|asc&page=0&page-size=15 '


    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()


def get_vpc_groups():
    token = get_token()

    # Get VPC Groups
    url = f'{base}/node/mo/uni/fabric/protpol.json?query-target=subtree'

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()


def get_static_paths(source_leaf_list):
    token = get_token()
    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    responses = []
    # Get VPC Groups
    for path in source_leaf_list:
        path_url = f"/paths-{path}"
        url = f'{base}/class/fvRsPathAtt.json?query-target-filter=wcard(fvRsPathAtt.tDn,"{path_url}")'
        requests.packages.urllib3.disable_warnings()
        response = requests.get(url, headers=headers, verify=False)
        responses.append(response.json())

    return responses


if __name__ == '__main__':
    # # Dump current config into backup file
    save_aci_config_snapshot()

    # Initialize Session with Cobra SDK and APIC
    ls = cobra.mit.session.LoginSession(apic, user, password)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()


    # Process input file
    with open(spec_file, 'r') as fp:
        Lines = fp.readlines()
        for line in Lines:
            line = line.replace(' ', '').replace('\n', '')
            if line and not line.startswith('#'): # Skip commented and blank lines

                # 1. Get the source and dest nodes, check they exist
                source_nodes = []
                dest_nodes = []
                vpc = False

                line = line.split(',')
                if len(line) == 2:
                    source_nodes.append(line[0])
                    dest_nodes.append(line[1])
                elif len(line) == 4:
                    source_nodes.append(line[0])
                    source_nodes.append(line[1])
                    dest_nodes.append(line[2])
                    dest_nodes.append(line[3])
                    vpc = True
                    source_nodes.sort(
                        key=int)  # Ensure the list is in ascending order (first node ID cannot be lower than 2nd ID)
                    dest_nodes.sort(
                        key=int)  # Ensure the list is in ascending order (first node ID cannot be lower than 2nd ID)
                else:
                    print(f'ERROR: Incorrect number of nodes!)'
                          f'Input received was {line}')
                    print('Please specify either 1 or 2 source/destination node IDs')
                    exit()

                # Check that Source Nodes Exist!
                target_nodes = source_nodes.copy()
                for node in target_nodes:
                    search_result = get_fabric_node_by_id(node)
                    if search_result['imdata']:
                        print(f'Found node (id={node})')
                    else:
                        print(f'Could NOT find Node with id={node}')
                        print('Exiting migration')
                        exit()

                # 2a. -----Switch profiles -------
                switch_profiles = get_leaf_switch_profiles()
                # Create Switch and Interface Profile for each Destination node
                for i in range(len(dest_nodes)):
                    # Initialize a list to store json data of destination profiles if they exist
                    dest_profiles = []
                    source_profiles = []
                    # 3a. Check if dest leaf has defined switch profile (checked via Leaf Selector Blocks)
                    for profile in switch_profiles['imdata']:
                        block_from = find_values('from_', json.dumps(profile))[0]
                        block_to = find_values('to_', json.dumps(profile))[0]
                        if block_from in source_nodes[i] and block_to in source_nodes[i]:
                            source_profiles.append(profile)
                        elif block_from in dest_nodes[i] and block_to in dest_nodes[i]:
                            dest_profiles.append(profile)

                    # 4a. If dest leaf switch profile undefined, create new one.
                    # 5a. Within leaf switch profile, create a switch selector with associated block and policy group
                    # 	Block is the destination NodeID and policy group would be the same policy group as the source leaf.
                    # 	(Current CU config shows no defined policy group so would just use fabric defaults)
                    # 6b. Within leaf switch profile, create a switch selector with associated block and policy group, and add new leaf interface profile.
                    policy_group = [obj['tDn'] for obj in find_values('infraRsAccNodePGrp', json.dumps(source_profiles))]
                    int_profile_name = f"{interface_profile_prefix}{dest_nodes[i]}"  # Needs to match when creating both switch profile and int profile
                    create_switch_profile(f'{dest_nodes[i]}', dest_nodes[i], dest_nodes[i], int_profile_tDn=f'uni/infra/accportprof-{int_profile_name}', policy_group_tDn=policy_group)

                    # 6. -----Interface Profiles------
                    # 7. Read source switch int profile, storing int profile and int selectors
                    # GET associated int profiles based on switch profile
                    source_int_profiles_tDns = []
                    for profile in source_profiles:
                        for child in profile['infraNodeP']['children']:
                            if 'infraRsAccPortP' in child:
                                source_int_profiles_tDns.append(child['infraRsAccPortP']['attributes']['tDn'])

                    all_interface_profiles = get_leaf_interface_profiles()
                    int_profiles = []
                    for profile in all_interface_profiles['imdata']:
                        if profile['infraAccPortP']['attributes']['dn'] in source_int_profiles_tDns:
                            int_profiles.append(profile)

                    # 8. Copy selector data from source int profile and create same selector data in dest int profile (exactly the same as source)
                    port_selectors = [] # List of port selector dicts
                    for profile in int_profiles:
                        for infraHPorts in profile['infraAccPortP']['children']:   # All children are infraHPorts
                            port_selector = {'blocks': [], "attributes": infraHPorts['infraHPortS']['attributes']}
                            for detail in infraHPorts['infraHPortS']['children']:
                                if 'infraRsAccBaseGrp' in detail.keys():
                                    port_selector['policy'] = detail['infraRsAccBaseGrp']['attributes']
                                elif 'infraPortBlk' in detail.keys():
                                    port_selector['blocks'].append(detail['infraPortBlk']['attributes'])
                            port_selectors.append(port_selector)
                    create_int_profile(int_profile_name, port_selectors)

                # If a pair is provided, create VPC protection group
                if vpc:
                    pods = md.lookupByClass("fabricExplicitGEp")
                    used_ids = []
                    for pod in pods:
                        used_ids.append(int(pod.id))

                    # Get the lowest unused Id
                    m = range(1, len(used_ids)+2)
                    id = min(set(m) - set(used_ids))
                    vpc_name = f"{vpc_group_prefix}{'-'.join([str(element) for element in dest_nodes])}"

                    # Create VPC Protection
                    create_vpc_group(vpc_name, id, dest_nodes, podId='1')

                # 9. ----Overlay----
                # 10. Cycle through Tenants and EPGs locating static path references to Paths from source leafs (will be in the the path data).
                # Create new paths using same encapsulation data but with updated path the new leaf.
                overlay_source_nodes = source_nodes.copy()
                overlay_dest_nodes = dest_nodes.copy()
                if vpc:
                    overlay_source_nodes.append(f'{source_nodes[0]}-{source_nodes[1]}')
                    overlay_dest_nodes.append(f'{dest_nodes[0]}-{dest_nodes[1]}')

                static_bindings_responses = get_static_paths(source_nodes)
                # print(static_bindings_responses)

                new_path_dicts = []
                # Create equivalent path for destination nodes
                for resp in static_bindings_responses:
                    for path in resp['imdata']:
                        # print(path['fvRsPathAtt']['attributes']['dn'])
                        new_path = json.dumps(path.copy())
                        for j in range(len(overlay_dest_nodes)):
                            # Need to replace references to the old path with the new one.
                            new_path = new_path.replace(f'paths-{overlay_source_nodes[j]}', f'paths-{overlay_dest_nodes[j]}')
                        new_path_dicts.append(json.loads(new_path))
                create_static_paths(new_path_dicts)
                print(f'Fabric Access Migration Complete for source nodes {source_nodes} and destination nodes {dest_nodes}')
    print("Complete Migration Complete. Please verify results through the APIC GUI")
    md.logout()
