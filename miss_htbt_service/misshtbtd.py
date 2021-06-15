#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2017-2020 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
# Copyright 2021 Samsung Electronics. All rights reserved.
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
import json
import multiprocessing
import os
import os.path as path
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
import yaml
import get_logger
import htbtworker as heartbeat
from mod import trapd_settings as tds
from mod.trapd_get_cbs_config import get_cbs_config

hb_properties_file = path.abspath(path.join(__file__, "../config/hbproperties.yaml"))

ABSOLUTE_PATH1 = path.abspath(path.join(__file__, "../htbtworker.py"))
ABSOLUTE_PATH2 = path.abspath(path.join(__file__, "../db_monitoring.py"))
ABSOLUTE_PATH3 = path.abspath(path.join(__file__, "../check_health.py"))
ABSOLUTE_PATH4 = path.abspath(path.join(__file__, "../cbs_polling.py"))


def create_database(update_db, jsfile, ip_address, port_num, user_name, password, db_name):
    from psycopg2 import connect
    try:
        con = connect(user=user_name, host=ip_address, password=password)
        database_name = db_name
        con.autocommit = True
        cur = con.cursor()
        query_value = "SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE datname = '%s'" % (database_name)
        cur.execute(query_value)
        not_exists_row = cur.fetchone()
        msg = "MSHBT:Create_database:DB not exists? ", not_exists_row
        _logger.info(msg)
        not_exists = not_exists_row[0]
        if not_exists is True:
            _logger.info("MSHBT:Creating database ...")
            query_value = "CREATE DATABASE %s" % (database_name)
            cur.execute(query_value)
        else:
            _logger.info("MSHBD:Database already exists")
        '''
        con = None
        con = connect(user=user_name, host = ip_address, password=password)
        database_name = db_name
        con.autocommit = True
        cur = con.cursor()
        cur.execute('CREATE DATABASE %s IF NOT EXISTS %s' %(database_name,database_name))
        '''
        cur.close()
        con.close()
    except(Exception) as err:
        msg = "MSHBD:DB Creation -", err
        _logger.error(msg)


# def get_pol_and_mr_urls(jsfile, pol_url, mr_url):
#    with open(jsfile, 'r') as outfile:
#        cfg = json.load(outfile)
#    mr_url = str(cfg['streams_subscribes']['ves-heartbeat']['dmaap_info']['topic_url'])
#    pol_url = str(cfg['streams_publishes']['dcae_cl_out']['dmaap_info']['topic_url'])

def read_hb_common(user_name, password, ip_address, port_num, db_name):
    envPytest = os.getenv('pytest', "")
    if (envPytest == 'test'):
        hbc_pid = 10
        hbc_srcName = "srvc_name"
        hbc_time = 1584595881
        hbc_state = "RUNNING"
        return hbc_pid, hbc_state, hbc_srcName, hbc_time
    connection_db = heartbeat.postgres_db_open(user_name, password, ip_address, port_num, db_name)
    cur = connection_db.cursor()
    query_value = "SELECT process_id,source_name,last_accessed_time,current_state FROM hb_common;"
    cur.execute(query_value)
    rows = cur.fetchall()
    hbc_pid = rows[0][0]
    hbc_srcName = rows[0][1]
    hbc_time = rows[0][2]
    hbc_state = rows[0][3]
    heartbeat.commit_and_close_db(connection_db)
    cur.close()
    return hbc_pid, hbc_state, hbc_srcName, hbc_time


def create_update_hb_common(update_flg, process_id, state, user_name, password, ip_address, port_num, db_name):
    current_time = int(round(time.time()))
    source_name = socket.gethostname()
    source_name = source_name + "-" + os.getenv('SERVICE_NAME', "")
    envPytest = os.getenv('pytest', "")
    if (envPytest != 'test'):
        connection_db = heartbeat.postgres_db_open(user_name, password, ip_address, port_num, db_name)
        cur = connection_db.cursor()
        if (heartbeat.db_table_creation_check(connection_db, "hb_common") == False):
            cur.execute("CREATE TABLE hb_common (PROCESS_ID integer primary key,SOURCE_NAME varchar,LAST_ACCESSED_TIME integer,CURRENT_STATE varchar);")
            query_value = "INSERT INTO hb_common VALUES(%d,'%s',%d,'%s');" % (process_id, source_name, current_time, state)
            _logger.info("MSHBT:Created hb_common DB and updated new values")
            cur.execute(query_value)
        if (update_flg == 1):
            query_value = "UPDATE hb_common SET PROCESS_ID='%d',SOURCE_NAME='%s', LAST_ACCESSED_TIME='%d',CURRENT_STATE='%s'" % (process_id, source_name, current_time, state)
            _logger.info("MSHBT:Updated  hb_common DB with new values")
            cur.execute(query_value)
        heartbeat.commit_and_close_db(connection_db)
        cur.close()


def create_update_vnf_table_1(jsfile, update_db, connection_db):
    with open(jsfile, 'r') as outfile:
        cfg = json.load(outfile)
    hbcfg = cfg['heartbeat_config']
    jhbcfg = json.loads(hbcfg)
    envPytest = os.getenv('pytest', "")
    if (envPytest == 'test'):
        vnf_list = ["Heartbeat_vDNS", "Heartbeat_vFW", "Heartbeat_xx"]
    else:
        cur = connection_db.cursor()
        if (heartbeat.db_table_creation_check(connection_db, "vnf_table_1") == False):
            cur.execute("CREATE TABLE vnf_table_1 (EVENT_NAME varchar primary key,HEARTBEAT_MISSED_COUNT integer,HEARTBEAT_INTERVAL integer,CLOSED_CONTROL_LOOP_NAME varchar,POLICY_VERSION varchar,POLICY_NAME varchar,POLICY_SCOPE varchar,TARGET_TYPE varchar,TARGET  varchar, VERSION varchar,SOURCE_NAME_COUNT integer,VALIDITY_FLAG integer);")
            _logger.info("MSHBT:Created vnf_table_1 table")
        if (update_db == 1):
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
        policyVersion = vnf['policyVersion']
        policyName = vnf['policyName']
        policyScope = vnf['policyScope']
        target_type = vnf['target_type']
        target = vnf['target']
        version = vnf['version']

        if (nfc not in vnf_list):
            query_value = "INSERT INTO vnf_table_1 VALUES('%s',%d,%d,'%s','%s','%s','%s','%s','%s','%s',%d,%d);" % (nfc, missed, intvl, clloop, policyVersion, policyName, policyScope, target_type, target, version, source_name_count, validity_flag)
        else:
            query_value = "UPDATE vnf_table_1 SET HEARTBEAT_MISSED_COUNT='%d',HEARTBEAT_INTERVAL='%d', CLOSED_CONTROL_LOOP_NAME='%s',POLICY_VERSION='%s',POLICY_NAME='%s', POLICY_SCOPE='%s',TARGET_TYPE='%s', TARGET='%s',VERSION='%s',VALIDITY_FLAG='%d' where EVENT_NAME='%s'" % (missed, intvl, clloop, policyVersion, policyName, policyScope, target_type, target, version, validity_flag, nfc)
        if (envPytest != 'test'):
            cur.execute(query_value)
    # heartbeat.commit_and_close_db(connection_db)
    if (envPytest != 'test'):
        cur.close()
    _logger.info("MSHBT:Updated vnf_table_1 as per the json configuration file")


def hb_cbs_polling_process(pid_current):
    subprocess.call([ABSOLUTE_PATH4, str(pid_current)])
    sys.stdout.flush()
    _logger.info("MSHBT:Creaated CBS polling process")
    return


def hb_worker_process(config_file_path):
    subprocess.call([ABSOLUTE_PATH1, config_file_path])
    sys.stdout.flush()
    _logger.info("MSHBT:Creaated Heartbeat worker process")
    return


def db_monitoring_process(current_pid, jsfile):
    subprocess.call([ABSOLUTE_PATH2, str(current_pid), jsfile])
    sys.stdout.flush()
    _logger.info("MSHBT:Creaated DB Monitoring process")
    return


def read_hb_properties_default():
    # Read the hbproperties.yaml for postgress and CBS related data
    s = open(hb_properties_file, 'r')
    a = yaml.full_load(s)

    if ((os.getenv('pg_ipAddress') is None) or (os.getenv('pg_portNum') is None) or (os.getenv('pg_userName') is None) or (os.getenv('pg_passwd') is None)):
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
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def read_hb_properties(jsfile):
    try:
        with open(jsfile, 'r') as outfile:
            cfg = json.load(outfile)
    except(Exception) as err:
        msg = "CBS Json file load error - ", err
        _logger.error(msg)
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
        consumer_id = str(cfg['consumerID'])
        group_id = str(cfg['groupID'])
        os.environ['consumerID'] = consumer_id
        os.environ['groupID'] = group_id
        if "SERVICE_NAME" in cfg:
            os.environ['SERVICE_NAME'] = str(cfg['SERVICE_NAME'])
    except(Exception) as err:
        msg = "CBS Json file read parameter error - ", err
        _logger.error(msg)
        return read_hb_properties_default()
    return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def fetch_json_file():
    if get_cbs_config():
        # current_runtime_config_file_name = tds.c_config['files.runtime_base_dir'] + "../etc/download.json"
        envPytest = os.getenv('pytest', "")
        if (envPytest == 'test'):
            current_runtime_config_file_name = "/tmp/opt/app/miss_htbt_service/etc/config.json"
        else:
            current_runtime_config_file_name = "../etc/download.json"
        msg = "MSHBD:current config logged to : %s" % current_runtime_config_file_name
        _logger.info(msg)
        with open(current_runtime_config_file_name, 'w') as outfile:
            json.dump(tds.c_config, outfile)
        if os.getenv('pytest', "") == 'test':
            jsfile = current_runtime_config_file_name
        else:
            jsfile = "../etc/config.json"
            os.system('cp ../etc/download.json ../etc/config.json')
            os.remove("../etc/download.json")
    else:
        msg = "MSHBD:CBS Config not available, using local config"
        _logger.warning(msg)
        my_file = Path("./etc/config.json")
        if my_file.is_file():
            jsfile = "./etc/config.json"
        else:
            jsfile = "../etc/config.json"
    msg = "MSHBT: The json file is - ", jsfile
    _logger.info(msg)
    return jsfile


def create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name):
    envPytest = os.getenv('pytest', "")
    if (envPytest != 'test'):  # pragma: no cover
        if (update_db == 0):
            create_database(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
        msg = "MSHBT: DB parameters -", ip_address, port_num, user_name, password, db_name
        _logger.info(msg)
        connection_db = heartbeat.postgres_db_open(user_name, password, ip_address, port_num, db_name)
        cur = connection_db.cursor()
        if (update_db == 0):
            if (heartbeat.db_table_creation_check(connection_db, "vnf_table_1") == False):
                create_update_vnf_table_1(jsfile, update_db, connection_db)
        else:
            create_update_vnf_table_1(jsfile, update_db, connection_db)
        heartbeat.commit_and_close_db(connection_db)
        cur.close()


def create_process(job_list, jsfile, pid_current):
    if (len(job_list) == 0):
        p1 = multiprocessing.Process(target=hb_worker_process, args=(jsfile,))
        time.sleep(1)
        p2 = multiprocessing.Process(target=db_monitoring_process, args=(pid_current, jsfile,))
        p1.start()
        time.sleep(1)
        p2.start()
        job_list.append(p1)
        job_list.append(p2)
        msg = "MSHBD:jobs list is", job_list
        _logger.info(msg)
    return job_list


_logger = get_logger.get_logger(__name__)


def main():
    try:
        subprocess.Popen([ABSOLUTE_PATH3], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        _logger.info("MSHBD:Execution Started")
        job_list = []
        pid_current = os.getpid()
        jsfile = fetch_json_file()
        ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = read_hb_properties(jsfile)
        msg = "MSHBT:HB Properties -", ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval
        _logger.info(msg)
        if (cbs_polling_required == 'True'):
            p3 = multiprocessing.Process(target=hb_cbs_polling_process, args=(pid_current,))
            p3.start()
        update_db = 0
        create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
        state = "RECONFIGURATION"
        update_flg = 0
        create_update_hb_common(update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name)
        msg = "MSHBD:Current process id is", pid_current
        _logger.info(msg)
        _logger.info("MSHBD:Now be in a continuous loop")
        i = 0
        while (True):
            hbc_pid, hbc_state, hbc_srcName, hbc_time = read_hb_common(user_name, password, ip_address, port_num, db_name)
            msg = "MSHBT: hb_common values ", hbc_pid, hbc_state, hbc_srcName, hbc_time
            _logger.info(msg)
            current_time = int(round(time.time()))
            time_difference = current_time - hbc_time
            msg = "MSHBD:pid,srcName,state,time,ctime,timeDiff is", hbc_pid, hbc_srcName, hbc_state, hbc_time, current_time, time_difference
            _logger.info(msg)
            source_name = socket.gethostname()
            source_name = source_name + "-" + str(os.getenv('SERVICE_NAME', ""))
            envPytest = os.getenv('pytest', "")
            if (envPytest == 'test'):
                if i == 2:
                    hbc_pid = pid_current
                    source_name = hbc_srcName
                    hbc_state = "RECONFIGURATION"
                elif (i > 3):
                    hbc_pid = pid_current
                    source_name = hbc_srcName
                    hbc_state = "RUNNING"
            if (time_difference < 60):
                if ((int(hbc_pid) == int(pid_current)) and (source_name == hbc_srcName)):
                    msg = "MSHBD:config status is", hbc_state
                    _logger.info(msg)
                    if (hbc_state == "RUNNING"):
                        state = "RUNNING"
                        update_flg = 1
                        create_update_hb_common(update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name)
                    elif (hbc_state == "RECONFIGURATION"):
                        _logger.info("MSHBD:Reconfiguration is in progress,Starting new processes by killing the present processes")
                        jsfile = fetch_json_file()
                        update_db = 1
                        create_update_db(update_db, jsfile, ip_address, port_num, user_name, password, db_name)
                        msg = "MSHBD: parameters  passed to DBM and HB are %d and %s", pid_current
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
                        state = "RUNNING"
                        update_flg = 1
                        create_update_hb_common(update_flg, pid_current, state, user_name, password, ip_address, port_num, db_name)

                else:
                    _logger.info("MSHBD:Inactive Instance: Process IDs are different, Keep Looping")
                    if (len(job_list) >= 2):
                        _logger.info("MSHBD:Inactive Instance: Main and DBM thread are waiting to become ACTIVE")
                    else:
                        jsfile = fetch_json_file()
                        msg = "MSHBD:Inactive Instance:Creating HB and DBM threads if not created already. The param pssed %d and %s", jsfile, pid_current
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
            else:
                _logger.info("MSHBD:Active instance is inactive for long time: Time to switchover")
                if ((int(hbc_pid) != int(pid_current)) or (source_name != hbc_srcName)):
                    _logger.info("MSHBD:Initiating to become Active Instance")
                    if (len(job_list) >= 2):
                        _logger.info("MSHBD:HB and DBM thread are waiting to become ACTIVE")
                    else:
                        jsfile = fetch_json_file()
                        msg = "MSHBD: Creating HB and DBM threads. The param pssed %d and %s", jsfile, pid_current
                        _logger.info(msg)
                        job_list = create_process(job_list, jsfile, pid_current)
                    hbc_pid, hbc_state, hbc_srcName, hbc_time = read_hb_common(user_name, password, ip_address, port_num, db_name)
                    update_flg = 1
                    create_update_hb_common(update_flg, pid_current, hbc_state, user_name, password, ip_address, port_num, db_name)
                else:
                    _logger.error("MSHBD:ERROR - Active instance is not updating hb_common in 60 sec - ERROR")
            time.sleep(25)
            if os.getenv('pytest', "") == 'test':
                i = i + 1
                if (i > 5):
                    _logger.info("Terminating main process for pytest")
                    p3.terminate()
                    time.sleep(1)
                    p3.join()
                    if (len(job_list) > 0):
                        job_list[0].terminate()
                        time.sleep(1)
                        job_list[0].join()
                        job_list.remove(job_list[0])
                    if (len(job_list) > 0):
                        job_list[0].terminate()
                        time.sleep(1)
                        job_list[0].join()
                        job_list.remove(job_list[0])
                    break

    except (Exception) as e:
        msg = "MSHBD:Exception as %s" % (str(traceback.format_exc()))
        _logger.error(msg)

        msg = "Fatal error. Could not start missing heartbeat service due to: {0}".format(e)
        _logger.error(msg)


if __name__ == '__main__':
    main()
