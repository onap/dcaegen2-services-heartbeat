# ============LICENSE_START=======================================================
# Copyright (c) 2020 AT&T Intellectual Property. All rights reserved.
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

from miss_htbt_service import config_notif

import tempfile, sys, json, os

def check_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval):
    assert(str(port_num) == "5432")
    assert(str(user_name) == "postgres")
    assert(str(db_name) == "postgres")
    assert(str(password) == "postgres")

def test_read_hb_properties_default():
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties_default()
    check_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_success():
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    testdata = { "pg_ipAddress": "10.0.0.99",
                 "pg_portNum": 65432,
                 "pg_dbName": "dbname",
                 "pg_userName": "pguser",
                 "pg_passwd": "pgpswd",
                 "CBS_polling_allowed": True,
                 "CBS_polling_interval": 30,
                 "SERVICE_NAME": "service_name"
    }
    json.dump(testdata, tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    assert(str(ip_address) == str(testdata["pg_ipAddress"]))
    assert(str(port_num) == str(testdata["pg_portNum"]))
    assert(str(user_name) == str(testdata["pg_userName"]))
    assert(str(password) == str(testdata["pg_passwd"]))
    assert(str(db_name) == str(testdata["pg_dbName"]))
    assert(str(cbs_polling_required) == str(testdata["CBS_polling_allowed"]))
    assert(str(cbs_polling_interval) == str(testdata["CBS_polling_interval"]))
    assert(str(os.environ['SERVICE_NAME']) == str(testdata["SERVICE_NAME"]))

def test_read_hb_properties_fail_bad_json():
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    print("bad json", file=tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    check_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_fail_missing_parameter():
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    testdata = { "pg_ipAddress": "10.0.0.99",
                 "pg_portNum": 65432,
                 "pg_dbName": "dbname",
                 "pg_userName": "pguser",
                 "pg_passwd": "pgpswd",
                 "CBS_polling_allowed": True,
                 "SERVICE_NAME": "service_name"
    }
    json.dump(testdata, tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    check_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_fail_():
    pass
def test_read_hb_properties_fail_():
    pass
