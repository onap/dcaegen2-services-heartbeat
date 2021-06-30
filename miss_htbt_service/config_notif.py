#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright 2018-2020 AT&T Intellectual Property, Inc. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
# Copyright 2021 Samsung Electronics. All rights reserved.
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
#
#  Author Prakash Hosangady (ph553f)
#  Read the hb_common table
#  Update the state to RECONFIGURATION and save the hb_common table

import os
import os.path as path
import socket
import yaml
import json
import time
import psycopg2

# use the fully qualified name here to let monkeypatching work
# from .mod.trapd_get_cbs_config import get_cbs_config
import mod.trapd_get_cbs_config
import mod.trapd_settings as tds

hb_properties_file = path.abspath(path.join(__file__, "../config/hbproperties.yaml"))


def postgres_db_open(username, password, host, port, database_name):
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        return True
    try:
        connection = psycopg2.connect(database=database_name, user=username, password=password, host=host, port=port)
    except Exception as e:
        print("HB_Notif::postgress connect error: %s" % e)
        connection = True
    return connection


def db_table_creation_check(connection_db, table_name):
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        return True
    cur = None
    try:
        cur = connection_db.cursor()
        cur.execute("SELECT * FROM information_schema.tables WHERE table_name = %s", (table_name,))
        database_names = cur.fetchone()
        if (database_names is not None) and (table_name in database_names):
            print(f"FOUND the table {table_name}")
            print("HB_Notif::Postgres already has table - %s" % table_name)
            return True
        else:
            print(f"did NOT find the table {table_name}")
            print("HB_Notif::Postgres does not have table - %s" % table_name)
            return False
    except psycopg2.DatabaseError as e:
        print('COMMON:Error %s' % e)
    finally:
        if cur:
            cur.close()


def commit_and_close_db(connection_db):
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        return True
    try:
        connection_db.commit()  # <--- makes sure the change is shown in the database
        connection_db.close()
        return True
    except psycopg2.DatabaseError as e:
        return False


def read_hb_properties_default():
    # Read the hbproperties.yaml for postgress and CBS related data
    s = open(hb_properties_file, 'r')
    a = yaml.full_load(s)
    if ((os.getenv('pg_ipAddress') is None) or (os.getenv('pg_portNum') is None) or (
            os.getenv('pg_userName') is None) or (os.getenv('pg_passwd') is None)):
        ip_address = a['pg_ipAddress']
        port_num = a['pg_portNum']
        user_name = a['pg_userName']
        password = a['pg_passwd']
    else:
        ip_address = os.getenv('pg_ipAddress')
        port_num = os.getenv('pg_portNum')
        user_name = os.getenv('pg_userName')
        password = os.getenv('pg_passwd')

    dbName = a['pg_dbName']
    db_name = dbName.lower()
    cbs_polling_required = a['CBS_polling_allowed']
    cbs_polling_interval = a['CBS_polling_interval']
    s.close()
    # TODO: there is a mismatch here between read_hb_properties_default and read_hb_properties.
    # read_hb_properties() forces all of the variables returned here to be strings, while the code here does not.
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def read_hb_properties(jsfile):
    try:
        with open(jsfile, 'r') as outfile:
            cfg = json.load(outfile)
    except Exception as err:
        print("Json file read error - %s" % err)
        return read_hb_properties_default()
    try:
        ip_address = str(cfg['pg_ipAddress'])
        port_num = str(cfg['pg_portNum'])
        user_name = str(cfg['pg_userName'])
        password = str(cfg['pg_passwd'])
        dbName = str(cfg['pg_dbName'])
        db_name = dbName.lower()
        cbs_polling_required = str(cfg['CBS_polling_allowed'])
        cbs_polling_interval = str(cfg['CBS_polling_interval'])
        if "SERVICE_NAME" in cfg:
            os.environ['SERVICE_NAME'] = str(cfg['SERVICE_NAME'])
    except Exception as err:
        print("Json file read parameter error - %s" % err)
        return read_hb_properties_default()
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def read_hb_common(user_name, password, ip_address, port_num, db_name):
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        hbc_pid = 10
        hbc_srcName = "srvc_name"
        hbc_time = 1541234567
        hbc_state = "RUNNING"
        return hbc_pid, hbc_state, hbc_srcName, hbc_time
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    cur.execute("SELECT process_id, source_name, last_accessed_time, current_state FROM hb_common")
    rows = cur.fetchall()
    # TODO: What if rows returned None or empty?
    print("HB_Notif::hb_common contents - %s" % rows)
    hbc_pid = rows[0][0]
    hbc_srcName = rows[0][1]
    hbc_time = rows[0][2]
    hbc_state = rows[0][3]
    commit_and_close_db(connection_db)
    cur.close()
    return hbc_pid, hbc_state, hbc_srcName, hbc_time


def update_hb_common(update_flg, process_id, state, user_name, password, ip_address, port_num, db_name):
    current_time = int(round(time.time()))
    source_name = socket.gethostname()
    source_name = source_name + "-" + str(os.getenv('SERVICE_NAME', ""))
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        return True
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    cur.execute("UPDATE hb_common SET LAST_ACCESSED_TIME = %s, CURRENT_STATE = %s WHERE "
                "PROCESS_ID = %s AND SOURCE_NAME = %s", (current_time, state, process_id, source_name))
    commit_and_close_db(connection_db)
    cur.close()
    return True


def fetch_json_file(download_json="../etc/download1.json", config_json="../etc/config.json"):
    # use the fully qualified name here to let monkeypatching work
    # if get_cbs_config():
    if mod.trapd_get_cbs_config.get_cbs_config():
        current_runtime_config_file_name = download_json
        envPytest = os.getenv('pytest', "")
        if envPytest == 'test':
            jsfile = "../etc/config.json"
            return jsfile
        print("Config_N:current config logged to : %s" % current_runtime_config_file_name)
        with open(current_runtime_config_file_name, 'w') as outfile:
            json.dump(tds.c_config, outfile)
        jsfile = current_runtime_config_file_name
    else:
        print("MSHBD:CBS Config not available, using local config")
        jsfile = config_json
    print("Config_N: The json file is - %s" % jsfile)
    return jsfile


def config_notif_run():
    jsfile = fetch_json_file()
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = read_hb_properties(
        jsfile)
    envPytest = os.getenv('pytest', "")
    if envPytest == 'test':
        return True
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    if db_table_creation_check(connection_db, "hb_common") is False:
        print("HB_Notif::ERROR::hb_common table not exists - No config download")
        connection_db.close()
    else:
        hbc_pid, hbc_state, hbc_srcName, hbc_time = read_hb_common(user_name, password, ip_address, port_num, db_name)
        state = "RECONFIGURATION"
        update_flg = 1
        ret = update_hb_common(update_flg, hbc_pid, state, user_name, password, ip_address, port_num, db_name)
        # TODO: There is no way for update_hb_common() to return false
        if ret:
            print("HB_Notif::hb_common table updated with RECONFIGURATION state")
            commit_and_close_db(connection_db)
            return True
        else:
            print("HB_Notif::Failure updating hb_common table")
            commit_and_close_db(connection_db)
            return False

    cur.close()
