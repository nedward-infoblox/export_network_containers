# MIT License

# Copyright (c) 2022 nedward-infoblox

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
import urllib3
import json
import time
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Variables -----------------------------------------|
# Grid credentials
gm_ip = '10.6.1.8'
gm_user = 'admin'
gm_pwd = 'infoblox'

net_view = 'default'
now = time.strftime('%I-%M-%S-%p')
outputfile = 'nc_{}.csv'.format(now)
q = f = []
c = 0
opt = {
    "domain-name": "domain_name",
    "domain-name-servers": "domain_name_servers",
    "routers": "routers",
    "broadcast-address": "broadcast_address"
}
key,value = "use_option",True
# ---------------------------------------------------|

# Fetch results from all pages --------------------------------------------|
def get_all_data(response):
    global c, q
    c = c + 1
    print("Found page: ",c)
    q = q + response['result']
    print("Total no of results: ",len(q))
    # if c == 4:
    #     return
    if "next_page_id" in response:
        print("Next page ID found in page",c)
        page_url = 'https://{}/wapi/v2.9/networkcontainer?_paging=1&_return_as_object=1&_page_id={}'.format(gm_ip,response['next_page_id'])
        p = requests.get(page_url, auth=(gm_user, gm_pwd), verify=False)
        p_output = json.loads(p.text)
        get_all_data(p_output)
    else:
        return
# -------------------------------------------------------------------------|

# Get list of all network containers ------------------------------|
url = 'https://{}/wapi/v2.9/networkcontainer?network_view={}&_paging=1&_return_as_object=1&_return_fields%2B=extattrs,options,comment,discovery_member,enable_discovery,enable_email_warnings,enable_snmp_warnings,mgm_private,high_water_mark,high_water_mark_reset,low_water_mark,low_water_mark_reset,zone_associations&_max_results=900'.format(gm_ip,net_view)
r1 = requests.get(url, auth=(gm_user, gm_pwd), verify=False)

if r1.status_code == 200:
    print ('OK!')
else:
    print ('Failed')
    print(r1, r1.text)
    exit()

r1_output = json.loads(r1.text)

get_all_data(r1_output)
# -----------------------------------------------------------------|

# Required fields -------------------------------------------------|
def append_fields(first):
    field_list = ["comment","discovery_member","domain_name","domain_name_servers","enable_discovery","enable_threshold_email_warnings","enable_threshold_snmp_warnings","mgm_private","network_view","range_high_water_mark","range_high_water_mark_reset","range_low_water_mark","range_low_water_mark_reset","routers","zone_associations","EA-City","EAInherited-City","EA-Country","EAInherited-Country","EA-Datacenter","EAInherited-Datacenter","EA-Description","EAInherited-Description"]
    new_fields = []
    for item in field_list:
        if item not in first:
            new_fields.append(item)
    new_keys = {element: None for element in new_fields}
    first.update(new_keys)
# -----------------------------------------------------------------|


for y in q:
    # Un-nest DHCP Options list to Infoblox CSV format
    p = {}
    op = y['options']
    for o in op:
        # print(o)
        if (key in o) and o[key] is True and o['name'] in opt:
                    p[opt[o['name']]] = o['value']
        else:
            n = "OPTION-{}".format(o['num'])
            p[n] = o['value']
    del y['options']
    y.update(p)

    # Un-nest EAs list to Infoblox CSV format
    g = {}
    ea = y['extattrs']
    for i,j in ea.items():
        k = "EA-{}".format(i)
        m = "EAInherited-{}".format(i)
        g[k] = j["value"]
        if 'inheritance_source' in j:
            g[m] = "INHERIT"
        else:
            g[m] = "OVERRIDE"
    del y['extattrs']

    # Change key names and values to match Infoblox CSV format ------------|
    del y['_ref']
    y['header-networkcontainer'] = 'networkcontainer'

    ip,mask = y['network'].split('/')
    y['address*'] = ip
    y['netmask*'] = mask
    del y['network']

    y['range_high_water_mark'] = y.pop('high_water_mark')
    y['range_high_water_mark_reset'] = y.pop('high_water_mark_reset')
    y['range_low_water_mark'] = y.pop('low_water_mark')
    y['range_low_water_mark_reset'] = y.pop('low_water_mark_reset')

    y['enable_threshold_email_warnings'] = y.pop('enable_email_warnings')
    y['enable_threshold_snmp_warnings'] = y.pop('enable_snmp_warnings')

    if 'zone_associations' in y:
        y['zone_associations'] = None
    # ---------------------------------------------------------------------|

    y.update(g)
    f.append(y)

# Populate empty fileds with null value ---------------------|
append_fields(f[0])

# To view the final JSON data, uncomment the bellow line
# print(f)
# -----------------------------------------------------------|

# Convert to csv file -------------------------------|
jsonfeed = json.dumps(f)
df = pd.read_json(jsonfeed)

head_nc = df['header-networkcontainer']
df = df.drop(columns=['header-networkcontainer'])
df.insert(loc=0, column='header-networkcontainer', value=head_nc)

df.to_csv(outputfile, encoding='utf-8', index=False)
# ---------------------------------------------------|
