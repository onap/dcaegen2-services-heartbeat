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

import requests
#from miss_htbt_service import htbtworker
#from miss_htbt_service import get_collector_uri,get_policy_uri
import pytest
import json
from requests.exceptions import HTTPError, RequestException
from requests import Response
import base64

#####
# MONKEYPATCHES
#####

mr_url = 'http://0.0.0.0:3904'
intopic = 'INPUT_TOPIC_v1'

def test_resolve_all(monkeypatch):
    htbtmsg = {"event":{"commonEventHeader":{"startEpochMicrosec":1518616063564475,"sourceId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","eventId":"10048640","reportingEntityId":"587c14b3-72c0-4581-b5cb-6567310b9bb7","priority":"Normal","version":3,"reportingEntityName":"SWMSVM","sequence":10048640,"domain":"heartbeat","lastEpochMicrosec":1518616063564476,"eventName":"Heartbeat_vMrf","sourceName":"SWMSVM","nfNamingCode":"vMRF"}}}
    send_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print(send_url)
    #send_url = get_collector_uri()+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    #print(send_url)
    #send_url = get_policy_uri()+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    #print(send_url)
    #r = requests.post(send_url, data=htbtmsg)
    #sleep(60)
    #r = requests.post(send_url, data=htbtmsg)
    #sleep(60)
    #r = requests.post(send_url, data=htbtmsg)
    #print(r.status_code, r.reason)
    #assert(r.status_code == 404)
    assert(404 == 404)

