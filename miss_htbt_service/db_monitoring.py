#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright 2018-2020 AT&T Intellectual Property, Inc. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
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
#  Author  Prakash Hosangady(ph553f)
#    DB Monitoring
#    Tracks Heartbeat messages on each of the VNFs stored in postgres DB
#    and generates Missing Heartbeat signal for Policy Engine

import json
import sys
import os
import socket
import time
import requests
import htbtworker as pm
import misshtbtd as db
import get_logger

_logger = get_logger.get_logger(__name__)


def sendControlLoopEvent(CLType, pol_url, policy_version, policy_name, policy_scope, target_type, srcName, epoc_time,
                         closed_control_loop_name, version, target):
    msg = "DBM:Time to raise Control Loop Event for Control loop typ /target type - ", CLType, target_type
    _logger.info(msg)
    if (CLType == "ONSET"):
        _logger.info("DBM:Heartbeat not received, raising alarm event")
        if (target_type == "VNF"):
            json_object = json.dumps({
                "closedLoopEventClient": "DCAE_Heartbeat_MS",
                "policyVersion": policy_version,
                "policyName": policy_name,
                "policyScope": policy_scope,
                "target_type": target_type,
                "AAI": {"generic-vnf.vnf-name": srcName},
                "closedLoopAlarmStart": epoc_time,
                "closedLoopEventStatus": "ONSET",
                "closedLoopControlName": closed_control_loop_name,
                "version": version,
                "target": target,
                "requestID": "8c1b8bd8-06f7-493f-8ed7-daaa4cc481bc",
                "from": "DCAE"
            });
        elif (target_type == "VM"):
            json_object = json.dumps({
                "closedLoopEventClient": "DCAE_Heartbeat_MS",
                "policyVersion": policy_version,
                "policyName": policy_name,
                "policyScope": policy_scope,
                "target_type": target_type,
                "AAI": {"vserver.vserver-name": srcName},
                "closedLoopAlarmStart": epoc_time,
                "closedLoopEventStatus": "ONSET",
                "closedLoopControlName": closed_control_loop_name,
                "version": version,
                "target": target,
                "requestID": "8c1b8bd8-06f7-493f-8ed7-daaa4cc481bc",
                "from": "DCAE"
            });
        else:
            return True
    elif (CLType == "ABATED"):
        _logger.info("DBM:Heartbeat received, clearing alarm event")
        # last_date_time = datetime.datetime.now()
        if (target_type == "VNF"):
            json_object = json.dumps({
                "closedLoopEventClient": "DCAE_Heartbeat_MS",
                "policyVersion": policy_version,
                "policyName": policy_name,
                "policyScope": policy_scope,
                "target_type": target_type,
                "AAI": {"generic-vnf.vnf-name": srcName},
                "closedLoopAlarmStart": epoc_time,
                "closedLoopEventStatus": "ABATED",
                "closedLoopControlName": closed_control_loop_name,
                "version": version,
                "target": target,
                "requestID": "8c1b8bd8-06f7-493f-8ed7-daaa4cc481bc",
                "from": "DCAE"
            });
        elif (target_type == "VM"):
            json_object = json.dumps({
                "closedLoopEventClient": "DCAE_Heartbeat_MS",
                "policyVersion": policy_version,
                "policyName": policy_name,
                "policyScope": policy_scope,
                "target_type": target_type,
                "AAI": {"vserver.vserver-name": srcName},
                "closedLoopAlarmStart": epoc_time,
                "closedLoopEventStatus": "ABATED",
                "closedLoopControlName": closed_control_loop_name,
                "version": version,
                "target": target,
                "requestID": "8c1b8bd8-06f7-493f-8ed7-daaa4cc481bc",
                "from": "DCAE"
            });
        else:
            return True
    else:
        return True
    payload = json_object
    msg = "DBM: CL Json object is", json_object
    _logger.info(msg)
    # psend_url = pol_url+'DefaultGroup/1?timeout=15000'
    psend_url = pol_url
    msg = "DBM:", psend_url
    _logger.info(msg)
    # Send response for policy on output topic
    try:
        r = requests.post(psend_url, data=payload)
        msg = "DBM:", r.status_code, r.reason
        _logger.info(msg)
        ret = r.status_code
        msg = "DBM:Status code for sending the control loop event is", ret
        _logger.info(msg)
    except(Exception) as err:
        msg = 'Message send failure : ', err
        _logger.error(msg)
    return True


def db_monitoring(current_pid, json_file, user_name, password, ip_address, port_num, db_name):
    while (True):
        time.sleep(20)

        envPytest = os.getenv('pytest', "")
        if (envPytest == 'test'):
            break

        try:
            with open(json_file, 'r') as outfile:
                cfg = json.load(outfile)
            pol_url = str(cfg['streams_publishes']['dcae_cl_out']['dmaap_info']['topic_url'])
        except(Exception) as err:
            msg = 'Json file process error : ', err
            _logger.error(msg)
            continue

        hbc_pid, hbc_state, hbc_srcName, hbc_time = db.read_hb_common(user_name, password, ip_address, port_num, db_name)
        source_name = socket.gethostname()
        source_name = source_name + "-" + str(os.getenv('SERVICE_NAME', ""))
        connection_db = pm.postgres_db_open(user_name, password, ip_address, port_num, db_name)
        cur = connection_db.cursor()
        if (int(current_pid) == int(hbc_pid) and source_name == hbc_srcName and hbc_state == "RUNNING"):
            _logger.info("DBM: Active DB Monitoring Instance")
            db_query = "Select event_name from vnf_table_1"
            cur.execute(db_query)
            vnf_list = [item[0] for item in cur.fetchall()]
            for event_name in vnf_list:
                query_value = "SELECT current_state FROM hb_common;"
                cur.execute(query_value)
                rows = cur.fetchall()
                hbc_state = rows[0][0]
                if (hbc_state == "RECONFIGURATION"):
                    _logger.info("DBM:Waiting for hb_common state to become RUNNING")
                    break

                db_query = "Select validity_flag,source_name_count,heartbeat_interval,heartbeat_missed_count,closed_control_loop_name,policy_version, policy_name,policy_scope, target_type,target,version from vnf_table_1 where event_name= '%s'" % (event_name)
                cur.execute(db_query)
                rows = cur.fetchall()
                validity_flag = rows[0][0]
                source_name_count = rows[0][1]
                heartbeat_interval = rows[0][2]
                heartbeat_missed_count = rows[0][3]
                closed_control_loop_name = rows[0][4]
                policy_version = rows[0][5]
                policy_name = rows[0][6]
                policy_scope = rows[0][7]
                target_type = rows[0][8]
                target = rows[0][9]
                version = rows[0][10]
                comparision_time = (heartbeat_interval * heartbeat_missed_count) * 1000
                if (validity_flag == 1):
                    for source_name_key in range(source_name_count):
                        epoc_time = int(round(time.time() * 1000))
                        epoc_query = "Select last_epo_time,source_name,cl_flag from vnf_table_2 where event_name= '%s' and source_name_key=%d" % (event_name, (source_name_key + 1))
                        cur.execute(epoc_query)
                        row = cur.fetchall()
                        if (len(row) == 0):
                            continue
                        epoc_time_sec = row[0][0]
                        srcName = row[0][1]
                        cl_flag = row[0][2]
                        if ((epoc_time - epoc_time_sec) > comparision_time and cl_flag == 0):
                            sendControlLoopEvent("ONSET", pol_url, policy_version, policy_name, policy_scope,
                                                 target_type, srcName, epoc_time, closed_control_loop_name, version,
                                                 target)
                            cl_flag = 1
                            update_query = "UPDATE vnf_table_2 SET CL_FLAG=%d where EVENT_NAME ='%s' and source_name_key=%d" % (cl_flag, event_name, (source_name_key + 1))
                            cur.execute(update_query)
                            connection_db.commit()
                        elif ((epoc_time - epoc_time_sec) < comparision_time and cl_flag == 1):
                            sendControlLoopEvent("ABATED", pol_url, policy_version, policy_name, policy_scope,
                                                 target_type, srcName, epoc_time, closed_control_loop_name, version,
                                                 target)
                            cl_flag = 0
                            update_query = "UPDATE vnf_table_2 SET CL_FLAG=%d where EVENT_NAME ='%s' and source_name_key=%d" % (cl_flag, event_name, (source_name_key + 1))
                            cur.execute(update_query)
                            connection_db.commit()

                else:  # pragma: no cover
                    msg = "DBM:DB Monitoring is ignored for %s since validity flag is 0" % (event_name)
                    _logger.info(msg)

                    delete_query_table2 = "DELETE FROM vnf_table_2 WHERE EVENT_NAME = '%s';" % (event_name)
                    cur.execute(delete_query_table2)
                    delete_query = "DELETE FROM vnf_table_1 WHERE EVENT_NAME = '%s';" % (event_name)
                    cur.execute(delete_query)
                    connection_db.commit()
                    """
                    Delete the VNF entry in table1 and delete all the source ids related to vnfs in table2
                    """
        else:  # pragma: no cover
            msg = "DBM:Inactive instance or hb_common state is not RUNNING"
            _logger.info(msg)
        pm.commit_and_close_db(connection_db)
        cur.close()
        break;


if __name__ == "__main__":
    _logger.info("DBM: DBM Process started")
    current_pid = sys.argv[1]
    jsfile = sys.argv[2]
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = db.read_hb_properties(jsfile)
    msg = "DBM:Parent process ID and json file name", current_pid, jsfile
    _logger.info(msg)
    while (True):
        db_monitoring(current_pid, jsfile, user_name, password, ip_address, port_num, db_name)
        envPytest = os.getenv('pytest', "")
        if (envPytest == 'test'):
            break
