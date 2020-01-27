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
# from miss_htbt_service.mod.trapd_get_cbs_config import get_cbs_config
import miss_htbt_service.mod.trapd_get_cbs_config
import miss_htbt_service.mod.trapd_settings

from . import monkey_psycopg2
import psycopg2
import tempfile, sys, json, os

def assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval):
    """
    used in the test_read_hb_properties*() tests
    """
    assert(str(port_num) == "5432")
    assert(str(user_name) == "postgres")
    assert(str(db_name) == "postgres")
    assert(str(password) == "postgres")

def test_read_hb_properties_default():
    """
    run read_hb_properties_default()
    """
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties_default()
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_success():
    """
    run read_hb_properties() to read properties from a file
    """
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
    """
    failure case for read_hb_properties: bad json in the file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    print("bad json", file=tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_read_hb_properties_fail_missing_parameter():
    """
    failure case for read_hb_properties: CBS_polling_allowed is missing
    """
    tmp = tempfile.NamedTemporaryFile(mode="w+")
    testdata = {
        "pg_ipAddress": "10.0.0.99",
        "pg_portNum": 65432,
        "pg_dbName": "dbname",
        "pg_userName": "pguser",
        "pg_passwd": "pgpswd",
        # "CBS_polling_allowed": True, # missing CBS_polling_allowed
        "CBS_polling_interval": 30,
        "SERVICE_NAME": "service_name"
    }
    json.dump(testdata, tmp)
    tmp.flush()
    ( ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval ) = config_notif.read_hb_properties(tmp.name)
    assert_default_values(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval)

def test_postgres_db_open(monkeypatch):
    """
    test postgres_db_open()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    
def test_postgres_db_open_fail(monkeypatch):
    """
    failure ase for postgres_db_open()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces(connect=True)
    dbconn = config_notif.postgres_db_open("test", "badpassword", "testsite", 5432, "dbname")
    assert(type(dbconn) is not monkey_psycopg2.MockConn)

def test_db_table_creation_check(monkeypatch):
    """
    test db_table_creation_check()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
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
    """
    test commit_and_close_db()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    print("commit_and_close_db(): no forced failures")
    ret = config_notif.commit_and_close_db(dbconn)
    assert(ret == True)

def test_commit_and_close_db_fail1(monkeypatch):
    """
    failure case for commit_and_close_db(): dbconn.close() fails
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    print("commit_and_close_db() - close failure")
    monkey_psycopg2.monkey_reset_forces(close=True)
    ret = config_notif.commit_and_close_db(dbconn)
    assert(ret == False)

def test_commit_and_close_db_fail2(monkeypatch):
    """
    failure case for commit_and_close_db(): dbconn.commit() fails
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    dbconn = config_notif.postgres_db_open("test", "testpswd", "testsite", 5432, "dbname")
    assert(type(dbconn) is monkey_psycopg2.MockConn)
    print("commit_and_close_db() - commit failure")
    monkey_psycopg2.monkey_reset_forces(commit=True)
    ret = config_notif.commit_and_close_db(dbconn)
    assert(ret == False)

def test_read_hb_properties_default(monkeypatch):
    """
    test read_hb_properties_default()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    monkey_psycopg2.monkey_set_defaults({
        "testdb1": {
            "hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

    output = config_notif.read_hb_common("test", "testpswd", "testsite", 5432, "testdb1")
    assert(output[0] == 1)
    assert(output[1] == "st1")
    assert(output[2] == "sn1")
    assert(output[3] == 31)
    
def test_update_hb_common(monkeypatch):
    """
    test update_hb_common()
    """
    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()
    output = config_notif.update_hb_common(None, 1234, "st1234", "test", "testpswd", "testsite", 5432, "testdb1")
    assert(output == True)

def monkeypatch_get_cbs_config_False():
    """
    monkeypatch for get_cbs_config() to force it to return False
    Required side affect: c_config is set to a json value
    """
    print("monkeypatch_get_cbs_config_False()")
    miss_htbt_service.mod.trapd_settings.c_config = { "patch": "false" }
    return False

def monkeypatch_get_cbs_config_True():
    """
    monkeypatch for get_cbs_config() to force it to return False
    Required side affect: c_config is set to a json value
    """
    print("monkeypatch_get_cbs_config_True()")
    miss_htbt_service.mod.trapd_settings.c_config = { "patch": "true" }
    return True

def test_fetch_json_file_get_cbs_config_is_true(monkeypatch):
    """
    test fetch_json_file() with get_cbs_config() returning True
    """
    monkeypatch.setattr(miss_htbt_service.mod.trapd_get_cbs_config, 'get_cbs_config', monkeypatch_get_cbs_config_True)
    tmp1 = tempfile.NamedTemporaryFile(mode="w+")
    tmp2 = tempfile.NamedTemporaryFile(mode="w+")
    output = config_notif.fetch_json_file(download_json = tmp1.name, config_json = tmp2.name)
    assert(output == tmp1.name)
    with open(tmp1.name, "r") as fp:
        j1 = json.load(fp)
    print(f"j1={j1}")
    assert("patch" in j1 and j1["patch"] == "true")

def test_fetch_json_file_get_cbs_config_is_false(monkeypatch):
    """
    test fetch_json_file() with get_cbs_config() returning False
    """
    monkeypatch.setattr(miss_htbt_service.mod.trapd_get_cbs_config, 'get_cbs_config', monkeypatch_get_cbs_config_False)
    tmp1 = tempfile.NamedTemporaryFile(mode="w+")
    tmp2 = tempfile.NamedTemporaryFile(mode="w+")
    output = config_notif.fetch_json_file(download_json = tmp1.name, config_json = tmp2.name)
    assert(output == tmp2.name)

FETCH_JSON_FILE = None

def monkeypatch_fetch_json_file():
    """
    Monkeypatch for fetch_json_file() to test config_notif_run()
    """
    print("monkeypatch_fetch_json_file()")
    return FETCH_JSON_FILE

def monkeypatch_return_False(*args, **kwargs):
    """
    Monkeypatch that can be used to force a function to return False
    """
    print("monkeypatch_return_False()")
    return False


def test_config_notif_run_good(monkeypatch):
    """
    test config_notif_run()
    everything good: "dbname" found (from below JSON info), "hb_common" listed in tables
    and hb_common has data.
    """
    monkeypatch.setattr(miss_htbt_service.config_notif, 'fetch_json_file', monkeypatch_fetch_json_file)

    tmp = tempfile.NamedTemporaryFile(mode="w+")
    global FETCH_JSON_FILE
    FETCH_JSON_FILE = tmp.name

    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()

    monkey_psycopg2.monkey_set_defaults({
        "dbname": {
            "from information_schema.tables": [
                [ "hb_common" ]
            ],
            "from hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

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
    
    output = config_notif.config_notif_run()
    print(f"output={output}")
    assert(output == True)

def test_config_notif_run_fail1(monkeypatch):
    """
    test config_notif_run()
    Failure case 1: "dbname" NOT found (from below JSON info), "hb_common" listed in tables
    and hb_common has data.
    """
    monkeypatch.setattr(miss_htbt_service.config_notif, 'fetch_json_file', monkeypatch_fetch_json_file)

    tmp = tempfile.NamedTemporaryFile(mode="w+")
    global FETCH_JSON_FILE
    FETCH_JSON_FILE = tmp.name

    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()

    monkey_psycopg2.monkey_set_defaults({
        "dbnameNOTHERE": {
            "from information_schema.tables": [
                [ "hb_common" ]
            ],
            "from hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

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
    
    output = config_notif.config_notif_run()
    print(f"output={output}")
    assert(output is None)

def test_config_notif_run_fail2(monkeypatch):
    """
    test config_notif_run()
    Failure case 2: "dbname" found (from below JSON info), "hb_common" NOT listed in tables
    and hb_common has data.
    """
    monkeypatch.setattr(miss_htbt_service.config_notif, 'fetch_json_file', monkeypatch_fetch_json_file)

    tmp = tempfile.NamedTemporaryFile(mode="w+")
    global FETCH_JSON_FILE
    FETCH_JSON_FILE = tmp.name

    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()

    monkey_psycopg2.monkey_set_defaults({
        "dbname": {
            "from information_schema.tables": [
                [ "hb_commonNOTHERE" ]
            ],
            "from hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

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
    
    output = config_notif.config_notif_run()
    print(f"output={output}")
    assert(output is None)

def test_config_notif_run_fail3(monkeypatch):
    """
    test config_notif_run()
    Failure case 3: "dbname" found (from below JSON info), "hb_common" listed in tables
    and update_hb_common() fails
    """
    monkeypatch.setattr(miss_htbt_service.config_notif, 'fetch_json_file', monkeypatch_fetch_json_file)
    monkeypatch.setattr(miss_htbt_service.config_notif, 'update_hb_common', monkeypatch_return_False)

    tmp = tempfile.NamedTemporaryFile(mode="w+")
    global FETCH_JSON_FILE
    FETCH_JSON_FILE = tmp.name

    monkeypatch.setattr(psycopg2, 'connect', monkey_psycopg2.monkey_connect)
    monkey_psycopg2.monkey_reset_forces()

    monkey_psycopg2.monkey_set_defaults({
        "dbname": {
            "from information_schema.tables": [
                [ "hb_common" ]
            ],
            "from hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })

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
    
    output = config_notif.config_notif_run()
    print(f"output={output}")
    assert(output == False)
