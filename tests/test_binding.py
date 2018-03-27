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
import pytest
import json
import base64
import errno
import imp
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
mr_url = 'http://mrrouter.att.com:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'OUTPUT_TOPIC_v1'

@httpretty.activate
def test_resolve_all(monkeypatch):
    #htbtmsg = "Find the best daily deals"
    htbtmsg = '{"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"SWMSVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vMrf","sourceName":"SWMSVM","nfNamingCode":"vMRF"}}}'
    send_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print(send_url)
    httpretty.register_uri(httpretty.GET, send_url, body=htbtmsg)
    #Use
    response = requests.get(send_url)
    print(response)
    print(response.text)
    assert(response.text == htbtmsg)
    try:
       os.makedirs('/tmp/config')
    except OSError as e:
      if e.errno != errno.EEXIST:
         raise 
    with open("/tmp/config/coll_ip.txt", "w") as file:
       #file.write('127.0.0.1')
       file.write('mytest.onap.org')
       file.close()
    with open("/tmp/config/coll_port.txt", "w") as file2:
       file2.write('3904')
       file2.close()
    #print(package_contents('miss_htbt_service'))
    #response = requests.get(send_url)
    #print(response)
    #print(response.text)
    #assert(response.text == htbtmsg)
    htbtmsg = json.dumps({"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"SWMSVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vMrf","sourceName":"SWMSVM","nfNamingCode":"vMRF"}}})
    send_url = htbtworker.get_collector_uri()+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print("Send URL : "+send_url)
    httpretty.register_uri(httpretty.GET, send_url, body=htbtmsg, content_type="application/json")
    pol_url = htbtworker.get_policy_uri()+'/events/'+outopic+'/DefaultGroup/1?timeout=15000'
    pol_body = json.dumps({"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"SWMSVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vMrf","sourceName":"SWMSVM","nfNamingCode":"vMRF"}}})
    print("Policy URL : "+pol_url)
    httpretty.register_uri(httpretty.POST, pol_url, body=pol_body, status=200, content_type='text/json')
    htbtworker.test_setup([send_url,send_url,3,60,intopic,outopic])
    ret = htbtworker.periodic_event()
    print("Returned",ret)
    assert(ret == 1)

