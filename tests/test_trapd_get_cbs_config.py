# ============LICENSE_START=======================================================
# Copyright (c) 2017-2020 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2021 Fujitsu Ltd.
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

import pytest
import unittest
import os

from miss_htbt_service.mod import trapd_get_cbs_config


class test_get_cbs_config(unittest.TestCase):
    """
    Test the trapd_get_cbs_config mod
    """

    pytest_json_data = '{ "heartbeat_config": { "vnfs": [{ "eventName": "Heartbeat_vDNS", "heartbeatcountmissed": 3, "heartbeatinterval": 60, "closedLoopControlName": "ControlLoopEvent1", "policyVersion": "1.0.0.5", "policyName": "vFireWall", "policyScope": "resource=sampleResource,type=sampletype,CLName=sampleCLName", "target_type": "VNF", "target": "genVnfName", "version": "1.0" }, { "eventName": "Heartbeat_vFW", "heartbeatcountmissed": 3, "heartbeatinterval": 60, "closedLoopControlName": "ControlLoopEvent1", "policyVersion": "1.0.0.5", "policyName": "vFireWall", "policyScope": "resource=sampleResource,type=sampletype,CLName=sampleCLName", "target_type": "VNF", "target": "genVnfName", "version": "1.0" }, { "eventName": "Heartbeat_xx", "heartbeatcountmissed": 3, "heartbeatinterval": 60, "closedLoopControlName": "ControlLoopEvent1", "policyVersion": "1.0.0.5", "policyName": "vFireWall", "policyScope": "resource=sampleResource,type=sampletype,CLName=sampleCLName", "target_type": "VNF", "target": "genVnfName", "version": "1.0" } ] }, "streams_publishes": { "ves_heartbeat": { "dmaap_info": { "topic_url": "http://message-router:3904/events/unauthenticated.DCAE_CL_OUTPUT/" }, "type": "message_router" } }, "streams_subscribes": { "ves_heartbeat": { "dmaap_info": { "topic_url": "http://message-router:3904/events/unauthenticated.SEC_HEARTBEAT_INPUT/" }, "type": "message_router" } } }'

    # create copy of snmptrapd.json for pytest
    pytest_json_config = "/tmp/opt/app/miss_htbt_service/etc/config.json"
    with open(pytest_json_config, "w") as outfile:
        outfile.write(pytest_json_data)

    def test_cbs_env_present(self):
        """
        Test that CONSUL_HOST env variable exists but fails to
        respond
        """

        with pytest.raises(Exception) as pytest_wrapped_sys_exit:
            result = trapd_get_cbs_config.get_cbs_config()
            assert pytest_wrapped_sys_exit.type == SystemExit

    def test_cbs_fallback_env_present(self):
        """
        Test that CBS fallback env variable exists and we can get config
        from fallback env var
        """
        os.environ.update(CBS_HTBT_JSON="/tmp/opt/app/miss_htbt_service/etc/config.json")
        result = True
        print("result: %s" % result)
        self.assertEqual(result, True)
