#!/usr/bin/env python
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

# list of packages that should be imported for this code to work
import cobra.mit.access
import cobra.mit.naming
import cobra.mit.request
import cobra.mit.session
import cobra.model.infra
from cobra.internal.codec.xmlcodec import toXMLStr
from config import *


def filter_dict_keys(org_dict, keep_keys):
    """Helper function to keep only certain keys from config.
    Pass in a dictionary and list of keys you wish to keep
    Any keys not in the list will be removed in the returned dictionary"""
    newDict = dict()
    # Iterate over all the items in dictionary and filter items which has even keys
    for (key, value) in org_dict.items():
        # Check if key is even then add pair to new dictionary
        if key in keep_keys:
            newDict[key] = value
    return newDict


def create_switch_profile(node_name, from_block, to_block, int_profile_tDn=None, policy_group_tDn=None):
    '''Function to create a switch profile (dn = "uni/infra/<nprof-<node>")
    :param node_name = naming of the underlay node (ex: Leaf101) to be used throughout
    :param to_block = block ID of the node. Same as from_blk when creating not vpc
    :param from_block = block ID of the node. Same as to_blk when creating not vpc
    :param policy_group_tDn = complete tDn of the desired associated policy group (ex:uni/infra/funcprof/accnodepgrp-SwPg)
    '''
    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession(apic, user, password)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    # the top level object on which operations will be made
    topDn = cobra.mit.naming.Dn.fromString(f'uni/infra/nprof-{switch_profile_prefix}{node_name}')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)

    # build the request using cobra syntax
    infraNodeP = cobra.model.infra.NodeP(topMo, annotation='', descr='', name=f'{switch_profile_prefix}{node_name}',
                                         nameAlias='', ownerKey='', ownerTag='')
    if int_profile_tDn:
        infraRsAccPortP = cobra.model.infra.RsAccPortP(infraNodeP, annotation='',
                                                       tDn=int_profile_tDn)  # Needs to be consistent w/ Int profile
    infraLeafS = cobra.model.infra.LeafS(infraNodeP, annotation='', descr='',
                                         name=f'{switch_selector_prefix}{node_name}', nameAlias='', ownerKey='',
                                         ownerTag='', type='range')
    if policy_group_tDn:
        infraRsAccNodePGrp = cobra.model.infra.RsAccNodePGrp(infraLeafS, annotation='', tDn=policy_group_tDn)
    infraNodeBlk = cobra.model.infra.NodeBlk(infraLeafS, annotation='', descr='', from_=from_block,
                                             name=f'{block_prefix}{node_name}', nameAlias='', to_=to_block)


    # commit the generated code to APIC
    # print(toXMLStr(topMo))
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    try:
        md.commit(c)
    except Exception as e:
        print(e)
        return

    print(f"Created Switch Profile {switch_profile_prefix}{node_name}")
    md.logout()
    return


def create_int_profile(name, port_selector_dicts):
    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession(apic, user, password)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    # the top level object on which operations will be made
    # topDn = cobra.mit.naming.Dn.fromString('uni/infra/accportprof-Leaf101')
    topDn = cobra.mit.naming.Dn.fromString(f'uni/infra/accportprof-{name}')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)

    # build the request using cobra syntax
    infraAccPortP = cobra.model.infra.AccPortP(topMo, annotation='', descr='', name=name, nameAlias='', ownerKey='',
                                               ownerTag='')

    # Keep only the keys which you can pass on to configuration
    limit_keys = ['annotation', 'descr', 'name', 'nameAlias', 'ownerKey', 'ownerTag', 'type', 'tDn', 'fexId',
                  'fromCard', 'fromPort', 'toCard', 'toPort']

    # Can have a range of port selectors
    # for i in range(len(port_selector_dicts)):
    for sel in port_selector_dicts:
        port_selector = filter_dict_keys(sel['attributes'], limit_keys)
        infraHPortS = cobra.model.infra.HPortS(infraAccPortP, **port_selector)
        if 'policy' in sel.keys():
            access_group = filter_dict_keys(sel['policy'], limit_keys)
            infraRsAccBaseGrp = cobra.model.infra.RsAccBaseGrp(infraHPortS, **access_group)
        for block in sel['blocks']:
            port_block = filter_dict_keys(block, limit_keys)
            infraPortBlk = cobra.model.infra.PortBlk(infraHPortS, **port_block)

    # commit the generated code to APIC
    # print(toXMLStr(topMo))
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    try:
        md.commit(c)
    except Exception as e:
        print(e)
        return

    print(f"Created Interface Profile {name}")
    md.logout()
    return


def create_vpc_group(name, id, nodes=[], podId='1'):
    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession(apic, user, password)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    # the top level object on which operations will be made
    # Replace the text below with the dn of your top object
    topDn = cobra.mit.naming.Dn.fromString(f'uni/fabric/protpol/expgep-{name}')
    # topDn = cobra.mit.naming.Dn.fromString(f'uni/fabric/protpol')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)


    # build the request using cobra syntax
    # fabricProtPol = cobra.model.fabric.ProtPol(topMo, annotation='', descr='VPC configuration', name='default',nameAlias='', ownerKey='', ownerTag='', pairT='explicit')
    fabricExplicitGEp = cobra.model.fabric.ExplicitGEp(topMo, annotation='', id=id, name=name)
    fabricRsVpcInstPol = cobra.model.fabric.RsVpcInstPol(fabricExplicitGEp, annotation='', tnVpcInstPolName='')
    fabricNodePEp = cobra.model.fabric.NodePEp(fabricExplicitGEp, annotation='', descr='', id=nodes[0], name='', nameAlias='', podId=podId)
    fabricNodePEp2 = cobra.model.fabric.NodePEp(fabricExplicitGEp, annotation='', descr='', id=nodes[1], name='', nameAlias='', podId=podId)

    # commit the generated code to APIC
    # print(toXMLStr(topMo))
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    md.commit(c)
    try:
        md.commit(c)
    except Exception as e:
        print(e)
        md.logout()
        return
    print(f"Created VPC Explicit Group {name} with ID {id} in pod {podId}")
    md.logout()


def create_static_paths(path_dicts):

    limit_keys = ['annotation', 'descr', 'encap', 'instrImedcy', 'mode', 'primaryEncap', 'tDn']

    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession(apic, user, password)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    path_names = [] # Track path names for printing

    # the top level object on which operations will be made
    # Confirm the dn below is for your top dn
    for path_dict in path_dicts:
        path_attributes = path_dict['fvRsPathAtt']['attributes']
        path_names.append(path_attributes['dn'])
        # topDn = cobra.mit.naming.Dn.fromString('uni/tn-InfrastructureMgmt_Services/ap-AP_InfrastructureMgmt_Services/epg-EPG_IMS_AIX/rspathAtt-[topology/pod-1/protpaths-107-108/pathep-[VPC1-DEN4A1F09-9040-MR9-SN78E7C0X]]')
        topDn = cobra.mit.naming.Dn.fromString(path_attributes['dn'])
        topParentDn = topDn.getParent()
        topMo = md.lookupByDn(topParentDn)

        # build the request using cobra syntax
        # fvRsPathAtt = cobra.model.fv.RsPathAtt(topMo, annotation='', descr='', encap='vlan-312', instrImedcy='immediate', mode='regular', primaryEncap='unknown', tDn='topology/pod-1/protpaths-107-108/pathep-[VPC1-DEN4A1F09-9040-MR9-SN78E7C0X]')
        path_attributes = filter_dict_keys(path_attributes, limit_keys)
        fvRsPathAtt = cobra.model.fv.RsPathAtt(topMo, **path_attributes)

        # commit the generated code to APIC
        # print(toXMLStr(topMo))
        c = cobra.mit.request.ConfigRequest()
        c.addMo(topMo)
        try:
            md.commit(c)
            # print(f"Created Static Path {path_attributes['dn']}")
        except Exception as e:
            print(f"ILLEGAL CONFIGURATION ERROR: {e}")
            # md.logout()

    print(f"Successfully Created Static Paths:\n {str(path_names)}")
    md.logout()
    return


