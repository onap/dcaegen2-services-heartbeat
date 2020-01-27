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

from . import monkey_psycopg2
import psycopg2
import tempfile, sys, json, os

def assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval):
    assert(str(port_num) == "5432")
    assert(str(user_name) == "postgres")
    assert(str(db_name) == "postgres")
    assert(str(password) == "postgres")

def test_read_hb_properties_default():
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties_default()
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_success():
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    testdata = {
        "pg_ipAddress": "10.0.0.99",
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
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_fail_missing_parameter():
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    testdata = {
        "pg_ipAddress": "10.0.0.99",
        "pg_portNum": 65432,
        "pg_dbName": "dbname",
        "pg_userName": "pguser",
        "pg_passwd": "pgpswd",
        # missing CBS_polling_allowed
        "CBS_polling_allowed": True,
        "SERVICE_NAME": "service_name"
    }
    json.dump(testdata, tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_postgres_db_open(monkeypatch):
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_psycopg2_connect)
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    
def test_postgres_db_open_fail(monkeypatch):
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_psycopg2_connect)
    dbconn = config_notif.postgres_db_open("test", "badpassword", "testsite", 5432, "dbname")
    assert(type(dbconn) is not monkey_psycopg2.MockConn)

def test_db_table_creation_check(monkeypatch):
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_psycopg2_connect)
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    dbconn.monkey_setDbInfo({ "select * from information_schema.tables": [ [ "testtable" ] ] })
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    ret = config_notif.db_table_creation_check(dbconn, "testtable")
    assert(ret == True)
    ret2 = config_notif.db_table_creation_check(dbconn, "missingtable")
    monkey_psycopg2.monkey_reset_forces(cursor=True)
    ret3 = config_notif.db_table_creation_check(dbconn, "testtable")
    assert(ret3 is None)
    
def test_commit_and_close_db(monkeypatch):
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_psycopg2_connect)
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    print("commit_and_close_db(): no forced failures")
    ret = config_notif.commit_and_close_db(dbconn)
    assert(ret == True)
    print("commit_and_close_db() - close failure")
    monkey_psycopg2.monkey_reset_forces(close=True)
    ret2 = config_notif.commit_and_close_db(dbconn)
    assert(ret2 == False)
    print("commit_and_close_db() - commit failure")
    monkey_psycopg2.monkey_reset_forces(commit=True)
    ret2 = config_notif.commit_and_close_db(dbconn)
    assert(ret2 == False)

def test_read_hb_properties_default(monkeypatch):
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_psycopg2_connect)
    monkey_psycopg2.monkey_psycopg2_set_defaults({
        "testdb1": {
            "hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

    output = config_notif.read_hb_common("test", "testpswd", "testsite", 5432, "testdb1")
    print(f"output={output}")
    assert(output[0] == 1)
    assert(output[1] == "st1")
    assert(output[2] == "sn1")
    assert(output[3] == 31)
    
