#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2021 Fujitsu Ltd.
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

import json
import os
import socket
import time

import psycopg2

import get_logger
from mod import trapd_settings as tds

_logger = get_logger.get_logger(__name__)
__docformat__ = 'restructuredtext'


def create_database(ip_address, user_name, password, db_name):
    """Create database for heartbeat service if not exists.

    :param str ip_address: PostgreSQL DB address
    :param str user_name: DB username
    :param str password: DB password
    :param str db_name: Database name to be created
    :return: None
    """
    try:
        con = psycopg2.connect(user=user_name, host=ip_address, password=password)
        database_name = db_name
        con.autocommit = True
        cur = con.cursor()
        query_value = "SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE datname = '%s'" % database_name
        cur.execute(query_value)
        not_exists_row = cur.fetchone()
        msg = "MSHBT: Create_database:DB not exists? ", not_exists_row
        _logger.info(msg)
        not_exists = not_exists_row[0]
        if not_exists:
            _logger.info("MSHBT: Creating database ...")
            query_value = "CREATE DATABASE %s" % database_name
            cur.execute(query_value)
        else:
            _logger.info("MSHBD: Database already exists")
        cur.close()
        con.close()
    except Exception as err:
        msg = "MSHBD: DB Creation -", err
        _logger.error(msg)


def postgres_db_open(username, password, host, port, database_name):
    """Create a database connection

    :param str username: DB username
    :param str password: DB password
    :param str host: DB host address
    :param int port: DB port number
    :param str database_name: Database name
    :return: psycopg2 connection object
    :rtype: psycopg2.connection
    """
    if tds.test_mode:
        return True
    connection = psycopg2.connect(database=database_name, user=username, password=password, host=host, port=port)
    return connection


def commit_db(connection_db):
    """Commit the current transaction.

    :param connection_db: Connection object
    :return: True if succeeded
    :rtype: bool
    """
    if tds.test_mode:
        return True
    try:
        connection_db.commit()  # <--- makes sure the change is shown in the database
        return True
    except psycopg2.DatabaseError as e:
        msg = 'COMMON:Error %s' % e
        _logger.error(msg)
        return False


def commit_and_close_db(connection_db):
    """Commit the current transaction and close connection.

    :param connection_db: Connection object
    :return: True if succeeded
    :rtype: bool
    """
    if tds.test_mode:
        return True
    try:
        connection_db.commit()  # <--- makes sure the change is shown in the database
        connection_db.close()
        return True
    except psycopg2.DatabaseError as e:
        msg = 'COMMON:Error %s' % e
        _logger.error(msg)
        return False


def create_update_hb_common(update_flg, process_id, state, user_name, password, ip_address, port_num, db_name):
    """Create or update hb_common table.

    :param int update_flg: Set 1 if update needed
    :param int process_id: Current process ID
    :param str state: Service state
    :param str user_name: DB user name
    :param str password: DB password
    :param str ip_address: DB host address
    :param int port_num: DB port number
    :param str db_name: Database name
    :return: None
    """
    current_time = int(round(time.time()))
    source_name = socket.gethostname()
    source_name = source_name + "-" + os.getenv('SERVICE_NAME', "")
    if tds.test_mode:
        return
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    if not db_table_creation_check(connection_db, "hb_common"):
        cur.execute(
            "CREATE TABLE hb_common (PROCESS_ID integer primary key,SOURCE_NAME varchar,LAST_ACCESSED_TIME integer,CURRENT_STATE varchar);")
        query_value = "INSERT INTO hb_common VALUES(%d,'%s',%d,'%s');" % (
            process_id, source_name, current_time, state)
        _logger.info("MSHBT:Created hb_common DB and updated new values")
        cur.execute(query_value)
    if update_flg == 1:
        query_value = "UPDATE hb_common SET PROCESS_ID='%d',SOURCE_NAME='%s', LAST_ACCESSED_TIME='%d',CURRENT_STATE='%s'" % (
            process_id, source_name, current_time, state)
        _logger.info("MSHBT:Updated  hb_common DB with new values")
        cur.execute(query_value)
    commit_and_close_db(connection_db)
    cur.close()


def create_update_vnf_table_1(jsfile, update_db, connection_db):
    """Create or update vnf_table_1 table.

    :param str jsfile: Path to config json file
    :param int update_db: Set 1 if update needed
    :param connection_db: Connection object
    :return: None
    """
    cur = None
    with open(jsfile, 'r') as outfile:
        cfg = json.load(outfile)
    hbcfg = cfg['heartbeat_config']
    jhbcfg = json.loads(hbcfg)
    if tds.test_mode:
        vnf_list = ["Heartbeat_vDNS", "Heartbeat_vFW", "Heartbeat_xx"]
    else:
        cur = connection_db.cursor()
        if not db_table_creation_check(connection_db, "vnf_table_1"):
            cur.execute(
                "CREATE TABLE vnf_table_1 (EVENT_NAME varchar primary key,HEARTBEAT_MISSED_COUNT integer,HEARTBEAT_INTERVAL integer,CLOSED_CONTROL_LOOP_NAME varchar,POLICY_VERSION varchar,POLICY_NAME varchar,POLICY_SCOPE varchar,TARGET_TYPE varchar,TARGET  varchar, VERSION varchar,SOURCE_NAME_COUNT integer,VALIDITY_FLAG integer);")
            _logger.info("MSHBT:Created vnf_table_1 table")
        if update_db == 1:
            query_value = "UPDATE vnf_table_1 SET VALIDITY_FLAG=0 where VALIDITY_FLAG=1;"
            cur.execute(query_value)
            _logger.info("MSHBT:Set Validity flag to zero in vnf_table_1 table")
        # Put some initial values into the queue
        db_query = "Select event_name from vnf_table_1"
        cur.execute(db_query)
        vnf_list = [item[0] for item in cur.fetchall()]
    for vnf in (jhbcfg['vnfs']):
        nfc = vnf['eventName']
        # _logger.error("MSHBT:",nfc)
        validity_flag = 1
        source_name_count = 0
        missed = vnf['heartbeatcountmissed']
        intvl = vnf['heartbeatinterval']
        clloop = vnf['closedLoopControlName']
        policy_version = vnf['policyVersion']
        policy_name = vnf['policyName']
        policy_scope = vnf['policyScope']
        target_type = vnf['target_type']
        target = vnf['target']
        version = vnf['version']

        if nfc not in vnf_list:
            query_value = "INSERT INTO vnf_table_1 VALUES('%s',%d,%d,'%s','%s','%s','%s','%s','%s','%s',%d,%d);" % (
                nfc, missed, intvl, clloop, policy_version, policy_name, policy_scope, target_type, target, version,
                source_name_count, validity_flag)
        else:
            query_value = "UPDATE vnf_table_1 SET HEARTBEAT_MISSED_COUNT='%d',HEARTBEAT_INTERVAL='%d', CLOSED_CONTROL_LOOP_NAME='%s',POLICY_VERSION='%s',POLICY_NAME='%s', POLICY_SCOPE='%s',TARGET_TYPE='%s', TARGET='%s',VERSION='%s',VALIDITY_FLAG='%d' where EVENT_NAME='%s'" % (
                missed, intvl, clloop, policy_version, policy_name, policy_scope, target_type, target, version,
                validity_flag,
                nfc)
        if not tds.test_mode:
            cur.execute(query_value)
    # heartbeat.commit_and_close_db(connection_db)
    if not tds.test_mode:
        cur.close()
    _logger.info("MSHBT:Updated vnf_table_1 as per the json configuration file")


def read_hb_common(user_name, password, ip_address, port_num, db_name):
    """Get a row from hb_common table.

    :param str user_name: DB user name
    :param str password: DB password
    :param str ip_address: DB host address
    :param int port_num: DB port number
    :param str db_name: Database name
    :return: Process ID, State, Source name, and last updated timestamp
    :rtype: tuple
    """
    if tds.test_mode:
        hbc_pid = 10
        hbc_src_name = "srvc_name"
        hbc_time = 1584595881
        hbc_state = "RUNNING"
        return hbc_pid, hbc_state, hbc_src_name, hbc_time
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    query_value = "SELECT process_id,source_name,last_accessed_time,current_state FROM hb_common;"
    cur.execute(query_value)
    rows = cur.fetchall()
    hbc_pid = rows[0][0]
    hbc_src_name = rows[0][1]
    hbc_time = rows[0][2]
    hbc_state = rows[0][3]
    commit_and_close_db(connection_db)
    cur.close()
    return hbc_pid, hbc_state, hbc_src_name, hbc_time


def create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name):
    """Create or update database and vnf_table_1 table.

    :param int update_db: Set 1 if update needed
    :param str jsfile: Path to config json file
    :param str ip_address: DB host address
    :param int port_num: DB port number
    :param str user_name: DB user name
    :param str password: DB password
    :param str db_name: Database name
    :return: None
    """
    if tds.test_mode:
        return
    if update_db == 0:
        create_database(ip_address, user_name, password, db_name)
    msg = "MSHBT: DB parameters -", ip_address, port_num, user_name, password, db_name
    _logger.info(msg)
    connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    if update_db == 0:
        if not db_table_creation_check(connection_db, "vnf_table_1"):
            create_update_vnf_table_1(jsfile, update_db, connection_db)
    else:
        create_update_vnf_table_1(jsfile, update_db, connection_db)
    commit_and_close_db(connection_db)
    cur.close()


def db_table_creation_check(connection_db, table_name):
    """Check if specified table exists.

    :param connection_db: Connection object
    :param str table_name: Table name to be checked
    :return: True if the table already exists
    :rtype: bool
    """
    if tds.test_mode:
        return True
    try:
        cur = connection_db.cursor()
        query_db = "select * from information_schema.tables where table_name='%s'" % table_name
        cur.execute(query_db)
        database_names = cur.fetchone()
        if database_names is not None:
            if table_name in database_names:
                return True
        else:
            return False
    except psycopg2.DatabaseError as e:
        msg = 'COMMON:Error %s' % e
        _logger.error(msg)
    finally:
        cur.close()
