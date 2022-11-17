#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2018-2022 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright (c) 2020 Deutsche Telekom. All rights reserved.
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

import logging

import psycopg2
import requests
import os
import os.path as path
import json
import sys
import time

import misshtbtd as db
import get_logger

_logger = logging.getLogger(__name__)

configjsonfile = "../etc/config.json"

def process_msg(cfgjsonfile, number_of_iterations=-1):
    """
        Function  to poll events from MR continuously
        and determine if matching configuration to be 
        tracked for missed HB function
    """
    
    global mr_url
    global configjsonfile
    configjsonfile = cfgjsonfile
    sleep_duration = 20
    reconfig_Flag = False
    while number_of_iterations != 0:
        number_of_iterations -= 1
        time.sleep(sleep_duration)
        print ("*** CFG json file info " + configjsonfile)        
        with open(configjsonfile, "r") as outfile:
            cfg = json.load(outfile)
        
        print ("*** CFG info " + str(cfg))
        mr_url = str(cfg["streams_subscribes"]["ves-heartbeat"]["dmaap_info"]["topic_url"])
        
        username = str(cfg["pg_userName"])
        password = str(cfg["pg_passwd"])
        db_host = str(cfg["pg_ipAddress"])
        db_port = cfg["pg_portNum"]
        database_name = str(cfg["pg_dbName"])
   
        reconfig_Flag = check_process_reconfiguration (username, password, db_host, db_port, database_name)
        eventname_list =  get_eventnamelist ()

        if "groupID" not in os.environ or "consumerID" not in os.environ:
            get_url = mr_url + "/DefaultGroup/1?timeout=15000"
        else:
            get_url = mr_url + "/" + os.getenv("groupID", "") + "/" + os.getenv("consumerID", "") + "?timeout=15000"
        msg = "HBT:Getting :" + get_url
        _logger.info(msg)

        try:
            res = requests.get(get_url)
        except Exception as e:
            # message-router may be down temporarily. continue polling loop to try again
            _logger.error("HBT: Failed to fetch messages from DMaaP. get_url=%s", get_url, exc_info=e)
            time.sleep(1)
            continue
        _logger.info("HBT: %s", res.text)
        input_string = res.text
        # If mrstatus in message body indicates some information, not json msg.
        if "mrstatus" in input_string:
            continue
        jlist = input_string.split("\n")
        print (jlist)
        # Process the DMaaP input message retrieved
        error = False
        jobj = []
        for line in jlist:
            try:
                jobj = json.loads(line)
            except ValueError:
                msg = "HBT:Decoding JSON has failed"
                _logger.error(msg)
                error = True
                break
        if error:
            continue
        if len(jobj) == 0:
            continue
        
        _logger.info("HBT jobj Array : %s", jobj)
        for item in jobj:
            srcname, lastepo, seqnum, event_name = parse_event(item)
            msg = "HBT:Newly received HB event values ::", event_name, lastepo, srcname
            _logger.info(msg)
            
            check_and_create_vnf2_table () 
            
            if event_name in eventname_list:  # pragma: no cover
                cur = sql_executor("SELECT source_name_count FROM vnf_table_1 WHERE event_name = %s", event_name)
                row = cur.fetchone()
                source_name_count = row[0]
                source_name_key = source_name_count + 1
                cl_flag = 0
                if source_name_count == 0:  # pragma: no cover
                    _logger.info("HBT: Insert entry into vnf_table_2, source_name='%s'", srcname)
                    new_vnf_entry(event_name, source_name_key, lastepo, srcname, cl_flag)
                else: # pragma: no cover
                    msg = "HBT:event name, source_name & source_name_count are", event_name, srcname, source_name_count
                    _logger.info(msg)
                    for source_name_key in range(source_name_count):
                        cur = sql_executor(
                            "SELECT source_name FROM vnf_table_2 WHERE event_name = %s AND " "source_name_key = %s",
                            event_name, (source_name_key + 1)
                        )
                        row = cur.fetchall()
                        if len(row) == 0:
                            continue
                        db_srcname = row[0][0]
                        if db_srcname == srcname:
                            msg = "HBT: Update vnf_table_2 : ", source_name_key, row
                            _logger.info(msg)
                            sql_executor(
                                "UPDATE vnf_table_2 SET LAST_EPO_TIME = %s, SOURCE_NAME = %s "
                                "WHERE EVENT_NAME = %s AND SOURCE_NAME_KEY = %s",
                                lastepo, srcname, event_name, (source_name_key + 1)
                            )
                            source_name_key = source_name_count
                            break
                        else:
                            continue
                    msg = "HBT: The source_name_key and source_name_count are ", source_name_key, source_name_count
                    _logger.info(msg)
                    if source_name_count == (source_name_key + 1):
                        source_name_key = source_name_count + 1
                        _logger.info("HBT: Insert entry into vnf_table_2, source_name='%s'", srcname)
                        new_vnf_entry(event_name, source_name_key, lastepo, srcname, cl_flag)
            else:
                _logger.info("HBT:eventName is not being monitored, Ignoring JSON message")
        msg = "HBT: Looping to check for new events from DMAAP"
        print ("HBT: Looping to check for new events from DMAAP")
        _logger.info(msg)

def new_vnf_entry (event_name, source_name_key, lastepo, srcname, cl_flag):
        """
        Wrapper function to update event to tracking tables
        """
    
        sql_executor(
            "INSERT INTO vnf_table_2 VALUES(%s,%s,%s,%s,%s)",
            event_name, source_name_key, lastepo, srcname, cl_flag
        )
        sql_executor(
            "UPDATE vnf_table_1 SET SOURCE_NAME_COUNT = %s WHERE EVENT_NAME = %s",
            source_name_key, event_name
        )   

def parse_event (jsonstring):
    """
    Function to parse incoming event as json object 
    and parse out required attributes
    """
    _logger.info("HBT jsonstring: %s", jsonstring)    
    #convert string to  object
    jitem = json.loads(jsonstring)
    
    try:
        srcname = jitem["event"]["commonEventHeader"]["sourceName"]
        lastepo = jitem["event"]["commonEventHeader"]["lastEpochMicrosec"]
        # if lastEpochMicrosec looks like microsec, align it with millisec
        if lastepo > 1000000000000000:
            lastepo = int(lastepo / 1000)
        seqnum = jitem["event"]["commonEventHeader"]["sequence"]
        event_name = jitem["event"]["commonEventHeader"]["eventName"]
        msg = "HBT:Newly received HB event values ::", event_name, lastepo, srcname
        _logger.info(msg)
        return (srcname,lastepo,seqnum,event_name)
    except Exception as err:
        msg = "HBT message process error - ", err
        _logger.error(msg)

def get_eventnamelist ():
    """
    Function to fetch active monitored eventname list
    """
    cur = sql_executor("SELECT event_name FROM vnf_table_1",)
    eventname_list = [item[0] for item in cur.fetchall()]
    msg = "\n\nHBT:eventnameList values ", eventname_list
    _logger.info(msg)
    return eventname_list

def check_and_create_vnf2_table ():
    """
    Check and create vnf_table_2 used for tracking HB entries
    """
    try:
        table_exist = False
        cur = sql_executor("SELECT * FROM information_schema.tables WHERE table_name = %s", "vnf_table_2")
        database_names = cur.fetchone()
        if database_names is not None:
            if "vnf_table_2" in database_names:
                table_exist = True
                
        if table_exist == False:
            msg = "HBT:Creating vnf_table_2"
            _logger.info(msg)
            sql_executor(
                """
                CREATE TABLE vnf_table_2 (
                    EVENT_NAME varchar,
                    SOURCE_NAME_KEY integer,
                    PRIMARY KEY(EVENT_NAME, SOURCE_NAME_KEY),
                    LAST_EPO_TIME BIGINT,
                    SOURCE_NAME varchar,
                    CL_FLAG integer
                )"""
            ,)
        else:
            msg = "HBT:vnf_table_2 is already there"
            _logger.info(msg)
        return True
    except psycopg2.DatabaseError as e:
        msg = "COMMON:Error %s" % e
        _logger.error(msg)
        return False
                
def check_process_reconfiguration(username, password, host, port, database_name):
    """
    Verify if DB configuration in progress
    """
    while True:
        hbc_pid, hbc_state, hbc_src_name, hbc_time = db.read_hb_common(
            username, password, host, port, database_name
        )
        if hbc_state == "RECONFIGURATION":
            _logger.info("HBT: RECONFIGURATION in-progress. Waiting for hb_common state to become RUNNING")
            time.sleep(10)
        else:
            _logger.info("HBT: hb_common state is RUNNING")
            break
    return False

def postgres_db_open():
    """
    Wrapper function for returning DB connection object 
    """
    
    global configjsonfile 

    (
        ip_address,
        port_num,
        user_name,
        password,
        db_name,
        cbs_polling_required,
        cbs_polling_interval,
    ) = db.read_hb_properties(configjsonfile)
    connection = psycopg2.connect(database=db_name, user=user_name, password=password, host=ip_address, port=port_num)
    return connection


def sql_executor (query, *values):
    """
    wrapper method for DB operation
    """        
    _logger.info("HBT query: %s values: %s", query, values)  
    
    connection_db = postgres_db_open()
    cur = connection_db.cursor()
    cur.execute(query, values) 
    update_commands = ["CREATE", "INSERT", "UPDATE"]
    if any (x in query for x in update_commands):
       try:
           connection_db.commit()  # <--- makes sure the change is shown in the database
       except psycopg2.DatabaseError as e:
           msg = "COMMON:Error %s" % e
           _logger.error(msg)
    return cur


def commit_and_close_db(connection_db):
    try:
        connection_db.commit()  # <--- makes sure the change is shown in the database
        connection_db.close()
        return True
    except psycopg2.DatabaseError as e:
        msg = "COMMON:Error %s" % e
        _logger.error(msg)
        return False


if __name__ == "__main__":
    get_logger.configure_logger("htbtworker")
    configjsonfile = sys.argv[1]
    msg = "HBT:HeartBeat thread Created"
    _logger.info("HBT:HeartBeat thread Created")
    msg = "HBT:The config file name passed is -%s",  configjsonfile
    _logger.info(msg)
    process_msg(configjsonfile)

