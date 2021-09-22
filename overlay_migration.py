import acitoolkit
from acitoolkit.acitoolkit import *
from config import *
# from pyaci import Node
import requests
import json



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


def get_static_paths():
    '''Gets all Non-Controller nodes (including both leafs and spines)'''

    token = get_token()
    # url = f"{base}/node/class/fvAEPg.json?query-target=subtree"
    url = f"{base}/node/class/fvAEPg.json?target-subtree-class=fvRsPathAtt&query-target=subtree"
    url = f"{base}/node/class/fvAEPg.json?query-target=subtree"

    # "/node/mo/uni/tn-[*]/ap-[*]/epg-[*].json?target-subtree-class=fvRsPathAtt"
    # url = f'{base}/node/class/fabricNode.json?query-target-filter=and(ne(fabricNode.role, %22controller%22), ge(fabricNode.id,%22101%22),le(fabricNode.id,%22202%22))'

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response.json()

if __name__ == '__main__':
    print(json.dumps(get_static_paths()))

    # session = Session(apic, user, password)
    # session.login()
    #
    #
    # epgs = EPG.get(session)
    # for epg in epgs:
    #     print(epg.get_json())
    #     epg.add_static_leaf_binding()

    # break



# tenants = Tenant.get(session)
# for tenant in tenants:
#     print(tenant.name)