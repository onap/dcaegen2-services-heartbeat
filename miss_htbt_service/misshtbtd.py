#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2017-2022 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright (c) 2020 Deutsche Telekom. All rights reserved.
# Copyright (c) 2021 Samsung Electronics. All rights reserved.
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
#
#  This is a main process that does the following
#  - Creates the CBS polling process that indicates the periodic download of
#    configuration file from CBS
#  - Creates heartbeat worker process that receives the Heartbeat messages from VNF
#  - Creates DB Monitoring process that generates Control loop event
#  - Download the CBS configuration and populate the DB
#
#  Author  Prakash Hosangady(ph553f@att.com)
import shutil
import logging
import traceback
import os
import sys
import json
import time
import multiprocessing
import subprocess
import yaml
import socket
import os.path as path
import tempfile
import psycopg2
from pathlib import Path

import check_health
import htbtworker as heartbeat
import get_logger
import cbs_polling
from mod import trapd_settings as tds
from mod.trapd_get_cbs_config import get_cbs_config

hb_properties_file = path.abspath(path.join(__file__, "../config/hbproperties.yaml"))
_logger = logging.getLogger(__name__)

ABSOLUTE_PATH1 = path.abspath(path.join(__file__, "../htbtworker.py"))
ABSOLUTE_PATH2 = path.abspath(path.join(__file__, "../db_monitoring.py"))
CONFIG_PATH = "../etc/config.json"


def create_database(update_db, jsfile, ip_address, port_num, user_name, password, db_name):
    from psycopg2 import connect

    try:
        con = connect(user=user_name, host=ip_address, password=password)
        database_name = db_name
        con.autocommit = True
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE datname = %s", (database_name,))
        not_exists_row = cur.fetchone()
        msg = "MSHBT:Create_database:DB not exists? ", not_exists_row
        _logger.info(msg)
        not_exists = not_exists_row[0]
        if not_exists is True:
            _logger.info("MSHBT:Creating database ...")
            cur.execute("CREATE DATABASE %s", (database_name,))
        else:
            _logger.info("MSHBD:Database already exists")
        cur.close()
        con.close()
    except Exception as err:
        msg = "MSHBD:DB Creation -", err
        _logger.error(msg)


def read_hb_common(user_name, password, ip_address, port_num, db_name):
    connection_db = heartbeat.postgres_db_open()
    cur = connection_db.cursor()
    cur.execute("SELECT process_id, source_name, last_accessed_time, current_state FROM hb_common")
    rows = cur.fetchall()
    hbc_pid = rows[0][0]
    hbc_src_name = rows[0][1]
    hbc_time = rows[0][2]
    hbc_state = rows[0][3]
    cur.close()
    return hbc_pid, hbc_state, hbc_src_name, hbc_time


def create_update_hb_common(update_flg, process_id, state, user_name, password, ip_address, port_num, db_name):
    current_time = int(round(time.time()))
    source_name = socket.gethostname()
    source_name = source_name + "-" + os.getenv("SERVICE_NAME", "")
    env_pytest = os.getenv("pytest", "")
    if env_pytest != "test":
        connection_db = heartbeat.postgres_db_open()
        cur = connection_db.cursor()
        if db_table_creation_check(connection_db, "hb_common") is False:
            cur.execute(
                """
                CREATE TABLE hb_common (
                    PROCESS_ID integer primary key,
                    SOURCE_NAME varchar,
                    LAST_ACCESSED_TIME integer,
                    CURRENT_STATE varchar
                )"""
            )
            cur.execute("INSERT INTO hb_common VALUES(%s, %s, %s, %s)", (process_id, source_name, current_time, state))
            _logger.info("MSHBT:Created hb_common DB and updated new values")
        elif update_flg == 1:
            cur.execute(
                "UPDATE hb_common SET LAST_ACCESSED_TIME = %s, CURRENT_STATE = %s "
                "WHERE PROCESS_ID = %s AND SOURCE_NAME = %s",
                (current_time, state, process_id, source_name),
            )
            _logger.info("MSHBT:Updated  hb_common DB with new values")
        # heartbeat.commit_and_close_db(connection_db)
        cur.close()

def db_table_creation_check(connection_db, table_name):
    cur = connection_db.cursor()
    try:
        cur.execute("SELECT * FROM information_schema.tables WHERE table_name = %s", (table_name,))
        database_names = cur.fetchone()
        if database_names is not None:
            if table_name in database_names:
                return True
        else:
            return False
    except psycopg2.DatabaseError as e:
        msg = "COMMON:Error %s" % e
        _logger.error(msg)
    finally:
        cur.close()
    
def create_update_vnf_table_1(jsfile, update_db, connection_db):
    with open(jsfile, "r") as outfile:
        cfg = json.load(outfile)
    hbcfg = cfg["heartbeat_config"]
    jhbcfg = json.loads(hbcfg)
    cur = connection_db.cursor()
    env_pytest = os.getenv("pytest", "")
    if env_pytest == "test":
        vnf_list = ["Heartbeat_vDNS", "Heartbeat_vFW", "Heartbeat_xx"]
    else:
        if db_table_creation_check(connection_db, "vnf_table_1") is False:
            cur.execute(
                """
                CREATE TABLE vnf_table_1 (
                    EVENT_NAME varchar primary key,
                    HEARTBEAT_MISSED_COUNT integer,
                    HEARTBEAT_INTERVAL integer,
                    CLOSED_CONTROL_LOOP_NAME varchar,
                    POLICY_VERSION varchar,
                    POLICY_NAME varchar,
                    POLICY_SCOPE varchar,
                    TARGET_TYPE varchar,
                    TARGET varchar,
                    VERSION varchar,
                    SOURCE_NAME_COUNT integer,
                    VALIDITY_FLAG integer
                )"""
            )
            _logger.info("MSHBT:Created vnf_table_1 table")
        if update_db == 1:
            cur.execute("UPDATE vnf_table_1 SET VALIDITY_FLAG=0 WHERE VALIDITY_FLAG=1")
            _logger.info("MSHBT:Set Validity flag to zero in vnf_table_1 table")
        # Put some initial values into the queue
        cur.execute("SELECT event_name FROM vnf_table_1")
        vnf_list = [item[0] for item in cur.fetchall()]
    for vnf in jhbcfg["vnfs"]:
        nfc = vnf["eventName"]
        validity_flag = 1
        source_name_count = 0
        missed = vnf["heartbeatcountmissed"]
        intvl = vnf["heartbeatinterval"]
        clloop = vnf["closedLoopControlName"]
        policy_version = vnf["policyVersion"]
        policy_name = vnf["policyName"]
        policy_scope = vnf["policyScope"]
        target_type = vnf["target_type"]
        target = vnf["target"]
        version = vnf["version"]

        if env_pytest == "test":
            # skip executing SQL in test
            continue
        if nfc not in vnf_list:
            cur.execute(
                "INSERT INTO vnf_table_1 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    nfc,
                    missed,
                    intvl,
                    clloop,
                    policy_version,
                    policy_name,
                    policy_scope,
                    target_type,
                    target,
                    version,
                    source_name_count,
                    validity_flag,
                ),
            )
            _logger.debug("Inserted new event_name = %s into vnf_table_1", nfc)
        else:
            cur.execute(
                """UPDATE vnf_table_1 SET HEARTBEAT_MISSED_COUNT = %s, HEARTBEAT_INTERVAL = %s,
                CLOSED_CONTROL_LOOP_NAME = %s, POLICY_VERSION = %s, POLICY_NAME = %s, POLICY_SCOPE = %s,
                TARGET_TYPE = %s, TARGET = %s, VERSION = %s, VALIDITY_FLAG = %s where EVENT_NAME = %s""",
                (
                    missed,
                    intvl,
                    clloop,
                    policy_version,
                    policy_name,
                    policy_scope,
                    target_type,
                    target,
                    version,
                    validity_flag,
                    nfc,
                ),
            )
    if env_pytest != "test":
        cur.close()
    _logger.info("MSHBT:Updated vnf_table_1 as per the json configuration file")


def hb_worker_process(config_file_path):
    subprocess.call([ABSOLUTE_PATH1, config_file_path])
    sys.stdout.flush()
    _logger.info("MSHBT:Created Heartbeat worker process")
    return


def db_monitoring_process(current_pid, jsfile):
    subprocess.call([ABSOLUTE_PATH2, str(current_pid), jsfile])
    sys.stdout.flush()
    _logger.info("MSHBT:Created DB Monitoring process")
    return


def read_hb_properties_default():
    # Read the hbproperties.yaml for postgress and CBS related data
    s = open(hb_properties_file, "r")
    a = yaml.full_load(s)

    if (
        (os.getenv("pg_ipAddress") is None)
        or (os.getenv("pg_portNum") is None)
        or (os.getenv("pg_userName") is None)
        or (os.getenv("pg_passwd") is None)
    ):
        ip_address = a["pg_ipAddress"]
        port_num = a["pg_portNum"]
        user_name = a["pg_userName"]
        password = a["pg_passwd"]
    else:
        ip_address = os.getenv("pg_ipAddress")
        port_num = os.getenv("pg_portNum")
        user_name = os.getenv("pg_userName")
        password = os.getenv("pg_passwd")

    db_name = a["pg_dbName"]
    db_name = db_name.lower()
    cbs_polling_required = a["CBS_polling_allowed"]
    cbs_polling_interval = a["CBS_polling_interval"]
    s.close()
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def read_hb_properties(jsfile):
    try:
        with open(jsfile, "r") as outfile:
            cfg = json.load(outfile)
    except Exception as err:
        msg = "CBS Json file load error - " + str(err)
        _logger.error(msg)
        return read_hb_properties_default()

    try:
        ip_address = str(cfg["pg_ipAddress"])
        port_num = str(cfg["pg_portNum"])
        user_name = str(cfg["pg_userName"])
        password = str(cfg["pg_passwd"])
        db_name = str(cfg["pg_dbName"])
        db_name = db_name.lower()
        cbs_polling_required = str(cfg["CBS_polling_allowed"])
        cbs_polling_interval = str(cfg["CBS_polling_interval"])
        consumer_id = str(cfg["consumerID"])
        group_id = str(cfg["groupID"])
        os.environ["consumerID"] = consumer_id
        os.environ["groupID"] = group_id
        if "SERVICE_NAME" in cfg:
            os.environ["SERVICE_NAME"] = str(cfg["SERVICE_NAME"])
    except Exception as err:
        msg = "CBS Json file read parameter error - " + str(err)
        _logger.error(msg)
        return read_hb_properties_default()
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def fetch_json_file() -> str:
    """Get configuration from CBS and save it to json file.

    :return: path to saved json file
    """
    # note: this func is called from multiple subprocesses. need to be thread-safe.
    jsfile = CONFIG_PATH
    # Try to get config from CBS. If succeeded, config json is stored to tds.c_config .
    if get_cbs_config():
        # Save config to temporary file
        with tempfile.NamedTemporaryFile("w", delete=False) as temp:
            _logger.info("MSHBD: New config saved to temp file %s", temp.name)
            json.dump(tds.c_config, temp)
        # Swap current config with downloaded config
        os.makedirs(Path(jsfile).parent, exist_ok=True)
        shutil.move(temp.name, jsfile)
    else:
        _logger.warning("MSHBD: CBS Config not available, using local config")
        local_config = "./etc/config.json"
        if Path(local_config).is_file():
            jsfile = local_config
    _logger.info("MSHBD: The json file is %s", jsfile)
    return jsfile


def create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name):
    env_pytest = os.getenv("pytest", "")
    if env_pytest != "test":  # pragma: no cover
        if update_db == 0:
            create_database(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
        msg = "MSHBT: DB parameters -", ip_address, port_num, user_name, password, db_name
        _logger.info(msg)
        connection_db = heartbeat.postgres_db_open()
        cur = connection_db.cursor()
        if update_db == 0:
            if db_table_creation_check(connection_db, "vnf_table_1") is False:
                create_update_vnf_table_1(jsfile, update_db, connection_db)
        else:
            create_update_vnf_table_1(jsfile, update_db, connection_db)
        #heartbeat.commit_and_close_db(connection_db)
        cur.close()


def create_process(job_list, jsfile, pid_current):
    if len(job_list) == 0:
        p1 = multiprocessing.Process(target=hb_worker_process, args=(jsfile,))
        time.sleep(1)
        p2 = multiprocessing.Process(
            target=db_monitoring_process,
            args=(
                pid_current,
                jsfile,
            ),
        )
        p1.start()
        time.sleep(1)
        p2.start()
        job_list.append(p1)
        job_list.append(p2)
        msg = "MSHBD:jobs list is", job_list
        _logger.info(msg)
    return job_list



def main():
    get_logger.configure_logger("misshtbtd")
    pid_current = os.getpid()
    hc_proc = multiprocessing.Process(target=check_health.start_health_check_server)
    cbs_polling_proc = multiprocessing.Process(target=cbs_polling.cbs_polling_loop, args=(pid_current,))
    try:
        _logger.info("MSHBD:Execution Started")
        # Start health check server
        hc_proc.start()
        _logger.info("MSHBD: Started health check server. PID=%d", hc_proc.pid)

        job_list = []
        jsfile = fetch_json_file()
        (
            ip_address,
            port_num,
            user_name,
            password,
            db_name,
            cbs_polling_required,
            cbs_polling_interval,
        ) = read_hb_properties(jsfile)
        msg = (
            "MSHBT:HB Properties -",
            ip_address,
            port_num,
            user_name,
            password,
            db_name,
            cbs_polling_required,
            cbs_polling_interval,
        )
        _logger.info(msg)
        update_db = 0
        create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
        state = "RECONFIGURATION"
        update_flg = 0
        create_update_hb_common(update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name)
        if cbs_polling_required == "True":
            # note: cbs_polling process must be started after `hb_common` table created
            cbs_polling_proc.start()
            _logger.info("MSHBD: Started CBS polling process. PID=%d", cbs_polling_proc.pid)
        _logger.info("MSHBD:Current process id is %d", pid_current)
        _logger.info("MSHBD:Now be in a continuous loop")
        i = 0
        while True:
            hbc_pid, hbc_state, hbc_src_name, hbc_time = read_hb_common(
                user_name, password, ip_address, port_num, db_name
            )
            msg = "MSHBT: hb_common values ", hbc_pid, hbc_state, hbc_src_name, hbc_time
            _logger.info(msg)
            current_time = int(round(time.time()))
            time_difference = current_time - hbc_time
            msg = (
                "MSHBD:pid,srcName,state,time,ctime,timeDiff is",
                hbc_pid,
                hbc_src_name,
                hbc_state,
                hbc_time,
                current_time,
                time_difference,
            )
            _logger.info(msg)
            source_name = socket.gethostname()
            source_name = source_name + "-" + str(os.getenv("SERVICE_NAME", ""))
            if time_difference < 60:
                if (int(hbc_pid) == int(pid_current)) and (source_name == hbc_src_name):
                    msg = "MSHBD:config status is", hbc_state
                    _logger.info(msg)
                    if hbc_state == "RUNNING":
                        state = "RUNNING"
                        update_flg = 1
                        create_update_hb_common(
                            update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name
                        )
                    elif hbc_state == "RECONFIGURATION":
                        _logger.info(
                            "MSHBD:Reconfiguration is in progress, "
                            "Starting new processes by killing the present processes"
                        )
                        jsfile = fetch_json_file()
                        update_db = 1
                        create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
                        msg = "MSHBD: parameters  passed to DBM and HB are %d and %s", pid_current
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
                        state = "RUNNING"
                        update_flg = 1
                        create_update_hb_common(
                            update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name
                        )

                else:
                    _logger.info("MSHBD:Inactive Instance: Process IDs are different, Keep Looping")
                    if len(job_list) >= 2:
                        _logger.info("MSHBD:Inactive Instance: Main and DBM thread are waiting to become ACTIVE")
                    else:
                        jsfile = fetch_json_file()
                        msg = (
                            "MSHBD:Inactive Instance:Creating HB and DBM threads if not created already. "
                            "The param passed %d and %s",
                            jsfile,
                            pid_current,
                        )
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
            else:
                _logger.info("MSHBD:Active instance is inactive for long time: Time to switchover")
                if (int(hbc_pid) != int(pid_current)) or (source_name != hbc_src_name):
                    _logger.info("MSHBD:Initiating to become Active Instance")
                    if len(job_list) >= 2:
                        _logger.info("MSHBD:HB and DBM thread are waiting to become ACTIVE")
                    else:
                        jsfile = fetch_json_file()
                        msg = "MSHBD: Creating HB and DBM threads. The param passed %d and %s", jsfile, pid_current
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
                    hbc_pid, hbc_state, hbc_src_name, hbc_time = read_hb_common(
                        user_name, password, ip_address, port_num, db_name
                    )
                    update_flg = 1
                    create_update_hb_common(
                        update_flg, pid_current, hbc_state, user_name, password, ip_address, port_num, db_name
                    )
                else:
                    _logger.error("MSHBD:ERROR - Active instance is not updating hb_common in 60 sec - ERROR")
            time.sleep(25)

    except Exception as e:
        msg = "MSHBD:Exception as %s" % (str(traceback.format_exc()))
        _logger.error(msg)

        msg = "Fatal error. Could not start missing heartbeat service due to: {0}".format(e)
        _logger.error(msg)
    finally:
        # Stop health check server
        if hc_proc.pid is not None:
            hc_proc.terminate()
            hc_proc.join()
        # Stop CBS polling process
        if cbs_polling_proc.pid is not None:
            cbs_polling_proc.terminate()
            cbs_polling_proc.join()


if __name__ == "__main__":
    main()
