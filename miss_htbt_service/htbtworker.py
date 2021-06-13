#!/usr/bin/env python3
# Copyright 2018-2020 AT&T Intellectual Property, Inc. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#  Author  Prakash Hosangady(ph553f@att.com)
#    Simple Microservice
#    Tracks Heartbeat messages on input topic in DMaaP
#    and poppulate the information in postgres DB

import json
import os
import os.path as path
import sys
import time

import requests

import get_logger
import htbtdb as db
import misshtbtd
from mod import trapd_settings as tds

_logger = get_logger.get_logger(__name__)


def read_json_file(i, prefix="../../tests"):
    if i == 0:
        with open(path.abspath(path.join(__file__, f"{prefix}/test1.json")), "r") as outfile:
            cfg = json.load(outfile)
    elif i == 1:
        with open(path.abspath(path.join(__file__, f"{prefix}/test2.json")), "r") as outfile:
            cfg = json.load(outfile)
    elif i == 2:
        with open(path.abspath(path.join(__file__, f"{prefix}/test3.json")), 'r') as outfile:
            cfg = json.load(outfile)
    return cfg


def process_msg(jsfile, user_name, password, ip_address, port_num, db_name):
    global mr_url
    i = 0
    sleep_duration = 20
    while True:
        time.sleep(sleep_duration)
        with open(jsfile, 'r') as outfile:
            cfg = json.load(outfile)
        mr_url = str(cfg['streams_subscribes']['ves-heartbeat']['dmaap_info']['topic_url'])

        while True:
            hbc_pid, hbc_state, hbc_src_name, hbc_time = db.read_hb_common(user_name, password, ip_address, port_num,
                                                                           db_name)
            if hbc_state == "RECONFIGURATION":
                _logger.info("HBT:Waiting for hb_common state to become RUNNING")
                time.sleep(10)
            else:
                break

        if tds.test_mode:
            eventname_list = ["Heartbeat_vDNS", "Heartbeat_vFW", "Heartbeat_xx"]
            connection_db = 0
        else:
            connection_db = db.postgres_db_open(user_name, password, ip_address, port_num, db_name)
            cur = connection_db.cursor()
            db_query = "Select event_name from vnf_table_1"
            cur.execute(db_query)
            eventname_list = [item[0] for item in cur.fetchall()]
        msg = "\n\nHBT:eventname_list values ", eventname_list
        _logger.info(msg)
        if "groupID" not in os.environ or "consumerID" not in os.environ:
            get_url = mr_url + '/DefaultGroup/1?timeout=15000'
        else:
            get_url = mr_url + '/' + os.getenv('groupID', "") + '/' + os.getenv('consumerID', "") + '?timeout=15000'
        msg = "HBT:Getting :" + get_url
        _logger.info(msg)

        if tds.test_mode:
            jsonobj = read_json_file(i)
            jobj = [jsonobj]
            i = i + 1
            msg = "HBT:newly received test message", jobj
            _logger.info(msg)
            if i >= 3:
                i = 0
                break
        else:
            res = requests.get(get_url)
            msg = "HBT:", res.text
            _logger.info(msg)
            input_string = res.text
            # If mrstatus in message body indicates some information, not json msg.
            if "mrstatus" in input_string:
                continue
            jlist = input_string.split('\n')
            # Process the DMaaP input message retreived
            error = False
            for line in jlist:
                try:
                    jobj = json.loads(line)
                except ValueError:
                    msg = 'HBT:Decoding JSON has failed'
                    _logger.error(msg)
                    error = True
                    break
            if error:
                continue
            if len(jobj) == 0:
                continue
        for item in jobj:
            try:
                if tds.test_mode:
                    jitem = jsonobj
                else:
                    jitem = json.loads(item)
                srcname = (jitem['event']['commonEventHeader']['sourceName'])
                lastepo = (jitem['event']['commonEventHeader']['lastEpochMicrosec'])
                seqnum = (jitem['event']['commonEventHeader']['sequence'])
                event_name = (jitem['event']['commonEventHeader']['eventName'])
            except Exception as err:
                msg = "HBT message process error - ", err
                _logger.error(msg)
                continue
            msg = "HBT:Newly received HB event values ::", event_name, lastepo, srcname
            _logger.info(msg)
            if not db.db_table_creation_check(connection_db, "vnf_table_2"):
                msg = "HBT:Creating vnf_table_2"
                _logger.info(msg)
                cur.execute(
                    "CREATE TABLE vnf_table_2 (EVENT_NAME varchar , SOURCE_NAME_KEY integer , PRIMARY KEY(EVENT_NAME,SOURCE_NAME_KEY),LAST_EPO_TIME BIGINT, SOURCE_NAME varchar, CL_FLAG integer);")
            else:
                msg = "HBT:vnf_table_2 is already there"
                _logger.info(msg)
            if event_name in eventname_list:  # pragma: no cover
                db_query = "Select source_name_count from vnf_table_1 where event_name='%s'" % event_name
                msg = "HBT:", db_query
                _logger.info(msg)
                if tds.test_mode:
                    break
                cur.execute(db_query)
                row = cur.fetchone()
                source_name_count = row[0]
                source_name_key = source_name_count + 1
                cl_flag = 0
                if source_name_count == 0:  # pragma: no cover
                    msg = "HBT: Insert entry in table_2,source_name_count=0 : ", row
                    _logger.info(msg)
                    query_value = "INSERT INTO vnf_table_2 VALUES('%s',%d,%d,'%s',%d);" % (
                    event_name, source_name_key, lastepo, srcname, cl_flag)
                    cur.execute(query_value)
                    update_query = "UPDATE vnf_table_1 SET SOURCE_NAME_COUNT='%d' where EVENT_NAME ='%s'" % (
                        source_name_key, event_name)
                    cur.execute(update_query)
                else:  # pragma: no cover
                    msg = "HBT:event name, source_name & source_name_count are", event_name, srcname, source_name_count
                    _logger.info(msg)
                    for source_name_key in range(source_name_count):
                        epoc_query = "Select source_name from vnf_table_2 where event_name= '%s' and source_name_key=%d" % (
                            event_name, (source_name_key + 1))
                        msg = "HBT:eppc query is", epoc_query
                        _logger.info(msg)
                        cur.execute(epoc_query)
                        row = cur.fetchall()
                        if len(row) == 0:
                            continue
                        db_srcname = row[0][0]
                        if db_srcname == srcname:
                            msg = "HBT: Update vnf_table_2 : ", source_name_key, row
                            _logger.info(msg)
                            update_query = "UPDATE vnf_table_2 SET LAST_EPO_TIME='%d',SOURCE_NAME='%s' where EVENT_NAME='%s' and SOURCE_NAME_KEY=%d" % (
                                lastepo, srcname, event_name, (source_name_key + 1))
                            cur.execute(update_query)
                            source_name_key = source_name_count
                            break
                        else:
                            continue
                    msg = "HBT: The source_name_key and source_name_count are ", source_name_key, source_name_count
                    _logger.info(msg)
                    if source_name_count == (source_name_key + 1):
                        source_name_key = source_name_count + 1
                        msg = "HBT: Insert entry in table_2 : ", row
                        _logger.info(msg)
                        insert_query = "INSERT INTO vnf_table_2 VALUES('%s',%d,%d,'%s',%d);" % (
                            event_name, source_name_key, lastepo, srcname, cl_flag)
                        cur.execute(insert_query)
                        update_query = "UPDATE vnf_table_1 SET SOURCE_NAME_COUNT='%d' where EVENT_NAME ='%s'" % (
                            source_name_key, event_name)
                        cur.execute(update_query)
            else:
                _logger.info("HBT:eventName is not being monitored, Igonoring JSON message")
        db.commit_db(connection_db)
        db.commit_and_close_db(connection_db)
        if not tds.test_mode:
            cur.close()


if __name__ == '__main__':
    jsfile = sys.argv[1]
    _logger.info("HBT:HeartBeat thread Created")
    msg = "HBT:The config file name passed is -%s", jsfile
    _logger.info(msg)
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = misshtbtd.read_hb_properties(
        jsfile)
    process_msg(jsfile, user_name, password, ip_address, port_num, db_name)
