# ACI Fabric Access Policy and Static Port Migration
An automation script that takes a source and destination node(s) in an ACI fabric and copies fabric access configuration (switch profiles, interface profiles, and VPC groups) from the source to the destination. This dramatically reduces migration time and error potential. 

Two solutions are provided: A python script and a collection of Ansible Playbooks.  

The script is intended for upgrading your infrastructure while maintaining the same fabric access policies in an active/active fashion. 
This mitigates the downtime and manual labour involved in migrating to the latest ACI leaf. 

The script takes source and destination node IDs as inputs. The output is a policy configuration for the destination nodes which matches the source node. 
The script create a new switch profile and interface profile(s) for the destination node based on the source node's configuration. 

The tested scope is leaf switches only, although it could be extended for spines as well.  

It is recommended that you begin with a single source-destination node pair in a test environment to ensure the new config is as-desired. 
There is no programmatic way to undo the new config. You would need to manually delete the new configs, so test before going to scale. 


## Contacts
* Andrew Dunsmoor (adunsmoo@cisco.com)
* Josh Proano (jproano@cisco.com)

## Solution Components
* ACI: SDK and REST API
* Ansible

## Workflow
The workflow for both solutions is similar. The objectives of the automation are as follows:

	1.	Get the source and dest nodes, check that they exist (in python script destination does not need to exist)
	2a.	-----Switch profiles ------- (if 1 destination leaf switch defined)
	3a.	Check if dest leaf has defined switch profile
	4a.	If dest leaf switch profile undefined, create new one. 
	5a.	Within new leaf switch profile, create a switch selector with associated block and policy group
	 
    2b.	-----Switch profiles ------- (if 2 destination leaf switch defined)
    3b. Create VPC Explicit Protection Group for the 2 dest leaf pairs
	4b.	Check if dest leaves has defined switch profile
	5b.	If dest leaf switch profile undefined, create new ones for each destination leaf. 
	6b.	Within leaf switch profile, create a switch selector with associated block and policy group, and add new leaf interface profile. 

	6.	-----Interface Profiles------
	7.	Read source switch int profile, storing int profile and int selectors
	8.	Copy selector data from source int profile and create same selector data in dest int profile (exactly the same as source)
	
	9.	----Overlay----
	10.	Cycle through Tenants and EPGs locating static path references to paths from source leafs. Create new paths using same encapsulation data but with updated path the new leaf. 

There are nuisance differences between the Ansible and Python implementations, they are not 1:1. But they each achieve the workflow outlined above.

## Verification

The script does not modify existing configs, and performs no delete operations. It only creates new configs, so the risk is low. However testing is still recommended.
A configuration snapshot is generated and can be found in the APIC under Admin -> Config Rollbacks
 
Verification of the results can be seen in the APIC GUI. The new configs will appear under:

FABRIC -> Access Policies -> Switches -> Leaf Switches -> Profiles

FABRIC -> Access Policies -> Interfaces -> Leaf Interfaces -> Profiles

FABRIC -> Access Policies -> Policies -> Switch -> Virtual Port Channel Default

Policies are re-used from the current config and the identical policy is simply applied to the new node. 
 

## Python Script

### Installation/Configuration

Install the project dependencies with "pip install -r requirements.txt"

ACI's Cobra SDK is also required. The version used is included and can be installed with:

"pip install acicobra-4.2_3h-py2.py3-none-any.whl"

"pip install acimodel-4.2_3h-py2.py3-none-any.whl"

More information on the ACI SDK can be found here: https://developer.cisco.com/docs/aci/#!cobra-sdk-downloads/download-cobra-sdk-files 

A config.py file must also be generated and completed. The required variables are as follows:

```python
#config.py
user = ''       # APIC Username
password = ''   # APIC Password

apic = 'https://<APIC-IP-ADDR>' # APIC Address 

base = apic+'/api'

spec_file = "MigrationTargets.txt"  # File to specify targets

# Specify your desired naming convention here. Node ID will be appended automatically. 
switch_profile_prefix = "SwPro_"       
interface_profile_prefix = "IntProf_"
switch_selector_prefix = "SwSel_"
block_prefix = "Block_"
```


### Usage

Specify your targets in the MigrationTargets.txt file before running. Formatting instructions are contained within.  

Run the script with:
'python3 fabric_migration.py'


## Ansible Script
 ACI Tenant Static Port Copy. This playbook will input a source leaf (or comma
 seperated pair) as well as a destination leaf (or comma seperated pair)
 the code will then proceed to iterate through all tenants and EPGs evaluating
 all the static binding path information. When static path infomration is found
 with the source nodes it is mutated and created with the same path data for the
 new desintation nodes. data is copied 1:1.
 
### Installation/Configuration

Ansible for Network Engineers quick start guide: https://docs.ansible.com/ansible/latest/network/getting_started/index.html#network-getting-started
 
NEED ansible-galaxy collection install cisco.aci
 
NEED to install jmespath (pip3) note the python3 interpreter in global vars

Cisco ACI Ansible guide: https://docs.ansible.com/ansible/latest/scenario_guides/guide_aci.html

### Usage
Use at your own risk! Use with a SIM before the real thing. Take snapshots and validate desired behavior.


Fabric Policies and Tenant Policies are migrated seperately in this Ansible implementation. 

For Fabric Access Policy migration, run playbook ACI-Leaf-FP-Migration.yml:

     ACI Leaf Copy Routine. This playbook will input a source leaf (or comma
     seperated pair) as well as a destination leaf (or comma seperated pair)
     the code will then proceed to check the existence of the new desintation
     node(s) that they have been registered into the fabric. Once validated the
     playbook will create needed Fabric Access policies and copy th access selector
     data from the source leafs into the destination leafs. The access selector
     data is copied 1:1. This works with PC and VPC policies as the new leaf
     switches are in a new VPC protection domain or stand alone.
     VERY IMPORTANT!!!!!     This playbook is built for an ACI fabric that was
     configured with 2 switch profiles and a single interface slector per switch
     profile (no combined VPC SP or IS) so please take into account any additional
     steps you may need based on your specific ACI configuration. 

     Example Execution of this playbook:
     
     ansible-playbook -i "10.94.164.69," ACI-Leaf-FP-Migration.yml --extra-vars '{"runtime_user":"aciuser,"runtime_pass":"acipass","runtime_source":"105,106","runtime_dest":"1105,1106"}'
     
     ^^^^^ Tested with Ansible v2.11.4

For Fabric Tenant Policy migration, run playbook ACI-Leaf-TP-Migration.yml:

     ACI Tenant Static Port Copy. This playbook will input a source leaf (or comma
     seperated pair) as well as a destination leaf (or comma seperated pair)
     the code will then proceed to iterate through all tenants and EPGs evaluating
     all the static binding path information. When static path infomration is found
     with the source nodes it is mutated and created with the same path data for the
     new desintation nodes. data is copied 1:1.
    
     Example Execution of this playbook:
     
     ansible-playbook -i "10.94.164.69," ACI-Leaf-TP-Migration.yml --extra-vars '{"runtime_user":"aciuser,"runtime_pass":"acipass","runtime_source":"105,106","runtime_dest":"1105,1106"}'
     
     ^^^^^ Tested with Ansible v2.11.4



# Screenshots

Source Interface profile (policy is copied but omitted for privacy)
![/IMAGES/source_int_profile.png](/IMAGES/source_int_profile.png)

Resulting Interface profile
![/IMAGES/source_int_profile.png](/IMAGES/source_int_profile.png)

## Further resources
Cisco ACI developer reference: https://developer.cisco.com/docs/aci/

Cobra SDK: https://cobra.readthedocs.io/en/latest/

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.