#!/usr/bin/env python3
# Copyright 2017 AT&T Intellectual Property, Inc. All rights reserved.
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
#  Author Prakash Hosangady (ph553f)
#  Read the hb_common table
#  Update the state to RECONFIGURATION and save the hb_common table

import os
import sched, datetime, time
import string
import sys
import socket
import yaml
import psycopg2
from pathlib import Path
import os.path as path

hb_properties_file =  path.abspath(path.join(__file__, "../config/hbproperties.yaml"))

def postgres_db_open(username,password,host,port,database_name):
    connection = psycopg2.connect(database=database_name, user = username, password = password, host = host, port =port)
    return connection

def db_table_creation_check(connection_db,table_name):
    try:
        cur = connection_db.cursor()
        query_db = "select * from information_schema.tables where table_name='%s'" %(table_name)
        cur.execute(query_db)
        database_names = cur.fetchone()
        if(database_names is not None):
            if(table_name in database_names):
                print("HB_Notif::Postgres has already has table -", table_name)
                return True
        else:
            print("HB_Notif::Postgres does not have table - ", table_name)
            return False
    except (psycopg2.DatabaseError, e):
        print('COMMON:Error %s' % e)
    finally:
        cur.close()

def commit_and_close_db(connection_db):
    try:
        connection_db.commit() # <--- makes sure the change is shown in the database
        connection_db.close()
        return True
    except(psycopg2.DatabaseError, e):
        return False

def read_hb_properties():
        #Read the hbproperties.yaml for postgress and CBS related data
        s=open(hb_properties_file, 'r')
        a=yaml.load(s)
        if((os.getenv('pg_ipAddress') is None) or (os.getenv('pg_portNum') is None) or (os.getenv('pg_userName') is None) or (os.getenv('pg_passwd') is None)):
           ip_address = a['pg_ipAddress']
           port_num = a['pg_portNum']
           user_name = a['pg_userName']
           password = a['pg_passwd']
        else:
          ip_address =  os.getenv('pg_ipAddress')
          port_num =  os.getenv('pg_portNum')
          user_name =  os.getenv('pg_userName')
          password =  os.getenv('pg_passwd')

        dbName = a['pg_dbName']
        db_name = dbName.lower()
        cbs_polling_required = a['CBS_polling_allowed']
        cbs_polling_interval = a['CBS_polling_interval']
        s.close()
        return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval

def read_hb_common(user_name,password,ip_address,port_num,db_name):
    connection_db = postgres_db_open(user_name,password,ip_address,port_num,db_name)
    cur = connection_db.cursor()
    query_value = "SELECT process_id,source_name,last_accessed_time,current_state FROM hb_common;"
    cur.execute(query_value)
    rows = cur.fetchall()
    print("HB_Notif::hb_common contents - ", rows)
    hbc_pid = rows[0][0]
    hbc_srcName = rows[0][1]
    hbc_time = rows[0][2]
    hbc_state = rows[0][3]
    commit_and_close_db(connection_db)
    cur.close()
    return hbc_pid, hbc_state, hbc_srcName, hbc_time

def update_hb_common(update_flg, process_id, state, user_name,password,ip_address,port_num,db_name):
    current_time = int(round(time.time()))
    source_name = socket.gethostname()
    source_name = source_name + "-" + str(os.getenv('SERVICE_NAME'))
    connection_db = postgres_db_open(user_name,password,ip_address,port_num,db_name)
    cur = connection_db.cursor()
    query_value = "UPDATE hb_common SET PROCESS_ID='%d',SOURCE_NAME='%s', LAST_ACCESSED_TIME='%d',CURRENT_STATE='%s'" %(process_id, source_name, current_time, state)
    cur.execute(query_value)
    commit_and_close_db(connection_db)
    cur.close()
    return True

#if __name__ == "__main__":
def config_notif_run():
   ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = read_hb_properties()
   connection_db = postgres_db_open(user_name,password,ip_address,port_num,db_name)
   cur = connection_db.cursor()
   if(db_table_creation_check(connection_db,"hb_common") == False):
      print("HB_Notif::ERROR::hb_common table not exists - No config download")
      connection_db.close()
   else:
      hbc_pid, hbc_state, hbc_srcName, hbc_time = read_hb_common(user_name,password,ip_address,port_num,db_name)
      state = "RECONFIGURATION"
      update_flg = 1
      ret = update_hb_common(update_flg, hbc_pid, state, user_name,password,ip_address,port_num,db_name)
      if (ret == True):
         print("HB_Notif::hb_common table updated with RECONFIGURATION state")
         commit_and_close_db(connection_db)
         return True
      else:
         print("HB_Notif::Failure updating hb_common table")
         commit_and_close_db(connection_db)
         return False
      
   cur.close()
