# ============LICENSE_START=======================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.

import os
import io
import requests
import httpretty
#import miss_htbt_service
from miss_htbt_service import htbtworker
#from miss_htbt_service.htbtworker import get_collector_uri,get_policy_uri
import subprocess
import pytest
import json
import base64
import errno
import imp
import time
from onap_dcae_cbs_docker_client.client import get_config


MODULE_EXTENSIONS = ('.py', '.pyc', '.pyo')

def package_contents(package_name):
    file, pathname, description = imp.find_module(package_name)
    if file:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0]
        for module in os.listdir(pathname)
        if module.endswith(MODULE_EXTENSIONS)])

#####
# MONKEYPATCHES
#####

#mr_url = 'http://127.0.0.1:3904'
mr_url = 'http://mrrouter.onap.org:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'POLICY-HILOTCA-EVENT-OUTPUT'

@httpretty.activate
def test_resolve_all(monkeypatch):
    #htbtmsg = "Find the best daily deals"
    htbtmsg = '{"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"TESTVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vVnf","sourceName":"TESTVM","nfNamingCode":"vVNF"}}}'
    send_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print(send_url)
    httpretty.register_uri(httpretty.GET, send_url, body=htbtmsg)
    #Use
    response = requests.get(send_url)
    print(response)
    print(response.text)
    assert(response.text == htbtmsg)
    htbtmsg = json.dumps({"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"TESTVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vVnf","sourceName":"TESTVM","nfNamingCode":"vVNF"}}})
    send_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print("Send URL : "+send_url)
    httpretty.register_uri(httpretty.GET, send_url, body=htbtmsg, content_type="application/json")
    pol_url = mr_url+'/events/'+outopic+'/DefaultGroup/1?timeout=15000'
    pol_body = json.dumps({"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"TESTVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vVnf","sourceName":"TESTVM","nfNamingCode":"vVNF"}}})
    print("Policy URL : "+pol_url)
    httpretty.register_uri(httpretty.POST, pol_url, body=pol_body, status=200, content_type='text/json')
    htbtworker.main([send_url,intopic,send_url,outopic,"vVNF",3,60,"internal_test"])
    ret = htbtworker.periodic_event()
    print("Returned",ret)
    assert(ret == 1)

def test_full():
    p = subprocess.Popen(['./miss_htbt_service/misshtbtd.py'],stdout=subprocess.PIPE)
    time.sleep(30)
    r = requests.get('http://127.0.0.1:10001')
    print(r.status_code)
    assert(r.status_code == 200)
