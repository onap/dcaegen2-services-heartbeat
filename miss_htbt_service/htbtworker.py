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

import psycopg2
import requests
import os
import os.path as path
import json,sys,time
import logging
import misshtbtd as db
import get_logger

_logger = get_logger.get_logger(__name__)

def read_json_file(i, prefix="../../tests"):
    if (i==0):
       with open (path.abspath(path.join(__file__, f"{prefix}/test1.json")), "r") as outfile:
          cfg = json.load(outfile)
    elif (i == 1):
       with open (path.abspath(path.join(__file__, f"{prefix}/test2.json")), "r") as outfile:
          cfg = json.load(outfile)
    elif (i ==2):
       with open( path.abspath(path.join(__file__, f"{prefix}/test3.json")), 'r') as outfile:
          cfg = json.load(outfile)
    return cfg

def process_msg(jsfile, user_name, password, ip_address, port_num, db_name):
    global mr_url
    i=0
    sleep_duration = 20
    while(True):
        time.sleep(sleep_duration)
        with open(jsfile, 'r') as outfile:
            cfg = json.load(outfile)
        mr_url = str(cfg['streams_subscribes']['ves-heartbeat']['dmaap_info']['topic_url'])

        while(True):
            hbc_pid, hbc_state, hbc_srcName, hbc_time = db.read_hb_common(user_name,password,ip_address,port_num,db_name)
            if(hbc_state == "RECONFIGURATION"):
                _logger.info("HBT:Waiting for hb_common state to become RUNNING")
                time.sleep(10)
            else:
                break

        if(os.getenv('pytest', "") == 'test'):
           eventnameList = ["Heartbeat_vDNS","Heartbeat_vFW","Heartbeat_xx"]
           connection_db = 0
        else:
           connection_db = postgres_db_open(user_name, password, ip_address, port_num, db_name)
           cur = connection_db.cursor()
           db_query = "Select event_name from vnf_table_1"
           cur.execute(db_query)
           eventnameList = [item[0] for item in cur.fetchall()]
        msg="\n\nHBT:eventnameList values ", eventnameList
        _logger.info(msg)
        if "groupID" not in os.environ or "consumerID" not in os.environ:
           get_url = mr_url + '/DefaultGroup/1?timeout=15000'
        else:
           get_url = mr_url + '/' + os.getenv('groupID', "") + '/' + os.getenv('consumerID', "") + '?timeout=15000'
        msg="HBT:Getting :"+get_url
        _logger.info(msg)

        if(os.getenv('pytest', "") == 'test'):
           jsonobj = read_json_file(i)
           jobj = []
           jobj.append(jsonobj)
           i=i+1
           msg="HBT:newly received test message", jobj
           _logger.info(msg)
           if (i >= 3):
              i=0
              break
        else:
           res = requests.get(get_url)
           msg="HBT:",res.text
           _logger.info(msg)
           inputString = res.text
           #If mrstatus in message body indicates some information, not json msg.
           if ("mrstatus" in inputString):
              continue
           jlist = inputString.split('\n');
           # Process the DMaaP input message retreived
           error = False
           for line in jlist:
               try:
                   jobj = json.loads(line)
               except ValueError:
                   msg='HBT:Decoding JSON has failed'
                   _logger.error(msg)
                   error = True
                   break
           if (error == True):
               continue
           if len(jobj) == 0:
               continue
        for item in jobj:
            try:
                if(os.getenv('pytest', "") == 'test'):
                    jitem = jsonobj
                else:
                    jitem = json.loads(item)
                srcname = (jitem['event']['commonEventHeader']['sourceName'])
                lastepo = (jitem['event']['commonEventHeader']['lastEpochMicrosec'])
                seqnum = (jitem['event']['commonEventHeader']['sequence'])
                eventName = (jitem['event']['commonEventHeader']['eventName'])
            except(Exception) as err:
                msg = "HBT message process error - ",err
                _logger.error(msg)
                continue
            msg="HBT:Newly received HB event values ::", eventName,lastepo,srcname
            _logger.info(msg)
            if(db_table_creation_check(connection_db,"vnf_table_2") ==False):
                 msg="HBT:Creating vnf_table_2"
                 _logger.info(msg)
                 cur.execute("CREATE TABLE vnf_table_2 (EVENT_NAME varchar , SOURCE_NAME_KEY integer , PRIMARY KEY(EVENT_NAME,SOURCE_NAME_KEY),LAST_EPO_TIME BIGINT, SOURCE_NAME varchar, CL_FLAG integer);")
            else:
                 msg="HBT:vnf_table_2 is already there"
                 _logger.info(msg)
            if(eventName in eventnameList):  #pragma: no cover
                    db_query = "Select source_name_count from vnf_table_1 where event_name='%s'" %(eventName)
                    msg="HBT:",db_query
                    _logger.info(msg)
                    if(os.getenv('pytest', "") == 'test'):
                       break
                    cur.execute(db_query)
                    row = cur.fetchone()
                    source_name_count = row[0]
                    source_name_key = source_name_count+1
                    cl_flag = 0
                    if(source_name_count==0): #pragma: no cover
                        msg="HBT: Insert entry in table_2,source_name_count=0 : ",row
                        _logger.info(msg)
                        query_value = "INSERT INTO vnf_table_2 VALUES('%s',%d,%d,'%s',%d);" %(eventName,source_name_key,lastepo,srcname,cl_flag)
                        cur.execute(query_value)
                        update_query = "UPDATE vnf_table_1 SET SOURCE_NAME_COUNT='%d' where EVENT_NAME ='%s'" %(source_name_key,eventName)
                        cur.execute(update_query)
                    else: #pragma: no cover
                        msg="HBT:event name, source_name & source_name_count are",eventName, srcname, source_name_count
                        _logger.info(msg)
                        for source_name_key in range(source_name_count):
                            epoc_query = "Select source_name from vnf_table_2 where event_name= '%s' and source_name_key=%d" %(eventName,(source_name_key+1))
                            msg="HBT:eppc query is",epoc_query
                            _logger.info(msg)
                            cur.execute(epoc_query)
                            row = cur.fetchall()
                            if (len(row)==0):
                                continue
                            db_srcname = row[0][0]
                            if (db_srcname == srcname):
                                msg="HBT: Update vnf_table_2 : ",source_name_key, row
                                _logger.info(msg)
                                update_query = "UPDATE vnf_table_2 SET LAST_EPO_TIME='%d',SOURCE_NAME='%s' where EVENT_NAME='%s' and SOURCE_NAME_KEY=%d" %(lastepo,srcname,eventName,(source_name_key+1))
                                cur.execute(update_query)
                                source_name_key = source_name_count
                                break
                            else:
                                continue
                        msg="HBT: The source_name_key and source_name_count are ", source_name_key, source_name_count
                        _logger.info(msg)
                        if (source_name_count == (source_name_key+1)):
                            source_name_key = source_name_count+1
                            msg="HBT: Insert entry in table_2 : ",row
                            _logger.info(msg)
                            insert_query = "INSERT INTO vnf_table_2 VALUES('%s',%d,%d,'%s',%d);" %(eventName,source_name_key,lastepo,srcname,cl_flag)
                            cur.execute(insert_query)
                            update_query = "UPDATE vnf_table_1 SET SOURCE_NAME_COUNT='%d' where EVENT_NAME ='%s'" %(source_name_key,eventName)
                            cur.execute(update_query)
            else:
                 _logger.info("HBT:eventName is not being monitored, Igonoring JSON message")
        commit_db(connection_db)
        commit_and_close_db(connection_db)
        if(os.getenv('pytest', "") != 'test'):
           cur.close()

def postgres_db_open(username,password,host,port,database_name):

    if(os.getenv('pytest', "") == 'test'):
        return True
    connection = psycopg2.connect(database=database_name, user = username, password = password, host = host, port =port)
    return connection

def db_table_creation_check(connection_db,table_name):
    if(os.getenv('pytest', "") == 'test'):
        return True
    try:
        cur = connection_db.cursor()
        query_db = "select * from information_schema.tables where table_name='%s'" %(table_name)
        cur.execute(query_db)
        database_names = cur.fetchone()
        if(database_names is not None):
            if(table_name in database_names):
                return True
        else:
            return False


    except psycopg2.DatabaseError as e:
        msg = 'COMMON:Error %s' % e
        _logger.error(msg)
    finally:
        cur.close()

def commit_db(connection_db):
    if(os.getenv('pytest', "") == 'test'):
        return True
    try:
        connection_db.commit() # <--- makes sure the change is shown in the database
        return True
    except psycopg2.DatabaseError as e:
        msg =  'COMMON:Error %s' % e
        _logger.error(msg)
        return False

def commit_and_close_db(connection_db):
    if(os.getenv('pytest', "") == 'test'):
        return True
    try:
        connection_db.commit() # <--- makes sure the change is shown in the database
        connection_db.close()
        return True
    except psycopg2.DatabaseError as e:
        msg = 'COMMON:Error %s' % e
        _logger.error(msg)
        return False

if __name__ == '__main__':
    jsfile = sys.argv[1]
    msg="HBT:HeartBeat thread Created"
    _logger.info("HBT:HeartBeat thread Created")
    msg="HBT:The config file name passed is -%s", jsfile
    _logger.info(msg)
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval= db.read_hb_properties(jsfile)
    process_msg(jsfile,user_name, password, ip_address, port_num, db_name)
