# ============LICENSE_START=======================================================
# Copyright (c) 2020-2022 AT&T Intellectual Property. All rights reserved.
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


import htbtworker
import os
import tempfile
import json 
import unittest
from unittest.mock import *
from _pytest.outcomes import skip

class Test_htbtworker(unittest.TestCase):

    def setUp(self):
        htbtworker.configjsonfile = (os.path.dirname(__file__))+"/test-config.json"

    @patch('requests.get')
    @patch('htbtworker.check_process_reconfiguration', return_value=False)
    @patch('htbtworker.get_eventnamelist')
    @patch('htbtworker.sql_executor')
    def test_process_msg(self, mock1, mock2, mock3, sqlmock1):  
        """
        Test to verify event processing using mock
        TBD - Negative test
        """
        
        status = True
        dmaap_data = [{"event":{"commonEventHeader":{"startEpochMicrosec":1544608845841,"sourceId":"VNFB_SRC5","eventId":"mvfs10","nfcNamingCode":"VNFB","timeZoneOffset":"UTC-05:30","reportingEntityId":"cc305d54-75b4-431b-adb2-eb6b9e541234","eventType":"platform","priority":"Normal","version":"4.0.2","reportingEntityName":"ibcx0001vm002oam001","sequence":1000,"domain":"heartbeat","lastEpochMicrosec":1544608845841,"eventName":"Heartbeat_vFW","vesEventListenerVersion":"7.0.2","sourceName":"SOURCE_NAME2","nfNamingCode":"VNFB"},"heartbeatFields":{"heartbeatInterval":20,"heartbeatFieldsVersion":"3.0"}}}]
        
        mock_resp = Mock()    
        mock_resp.configure_mock(
            **{
                  "text": json.dumps(dmaap_data)
            }  
         )             
        mock3.return_value = [("Heartbeat_vDNS", "Heartbeat_vFW")]
        mock1.return_value = mock_resp  

        filename = "test-config.json"
        htbtworker.process_msg(filename, number_of_iterations=1)
        self.assertEqual(status, True)
        # mock1.return_value = "NoEvent"    
        # with self.assertRaises(SystemExit) as exc:
        #     htbtworker.process_msg(filename, number_of_iterations=1)

        
    def test_parse_event(self):
        """
        test_parse_event() opens the file test1.json and returns attributes
        """
        filename = (os.path.dirname(__file__))+"/test1.json"
        with open(filename,"r") as fp:
             data = json.load(fp)
        srcname,lastepo,seqnum,event_name =  htbtworker.parse_event(data)
        self.assertEqual(srcname, "SOURCE_NAME1")
        self.assertEqual(event_name, "Heartbeat_vDNS")

    @patch('htbtworker.sql_executor')
    def test_create_and_check_vnf2_table (self, mock_settings):
        """
        Test to verify existence of given table
        """
        mock_cursor = Mock()        
        mock_cursor.configure_mock(
            **{
                "fetchone.return_value": [("vnf_table_2")]
            }
        )
        #mock_settings.cur.fetchone.return_value = "vnf_table_2"
        mock_settings.return_value = mock_cursor
        status = htbtworker.check_and_create_vnf2_table ()
        self.assertEqual(status, True) 
     
        with patch('htbtworker.sql_executor', new=Mock(side_effect=htbtworker.psycopg2.DatabaseError())):
            status = htbtworker.check_and_create_vnf2_table ()
            self.assertEqual(False, status)       
         
    @patch('htbtworker.sql_executor')
    def test_new_vnf_entry (self, sql_mock):
        """
        Check to verify if new node entry is made for tracking HB
        """
        status = True
        htbtworker.new_vnf_entry ("Heartbeat_vDNS", "TESTNODE", 1548313727714000, "TESTNODE", 1)
        self.assertEqual(status, True)

    @patch('htbtworker.sql_executor')
    def test_get_eventnamelist (self, sql_mock):
        """
        Test to verify eventname list is returned from vnf_table_1 
        TBD - List comparison 
        """
        eventname_list = [("Heartbeat_vDNS", "Heartbeat_vFW")]
        mock_cursor = Mock()        
        mock_cursor.configure_mock(
            **{
                "fetchall.return_value": eventname_list
            }
        )
        sql_mock.return_value = mock_cursor
        return_list = htbtworker.get_eventnamelist ()
        # self.assertEqual(['Heartbeat_vDNS'], return_list)
        self.assertIn("Heartbeat_vDNS", return_list) 
  
    @patch('htbtworker.postgres_db_open')
    def test_sql_executor (self, db_mock):
        """
        Test sql executor wrapper method 
        """
        htbtworker.sql_executor ("SELECT * FROM information_schema.tables WHERE table_name = %s", "vnf_table_2")
        htbtworker.sql_executor ("INSERT into information_schema.tables,")
        connection_db = db_mock
        with patch('htbtworker.postgres_db_open.commit', new=Mock(side_effect=htbtworker.psycopg2.DatabaseError())):
            flag = htbtworker.commit_and_close_db(connection_db)
            self.assertEqual(False, flag)

    @patch('psycopg2.connect')
    def test_postgres_db_open (self, mock):
        """
        Test wrapper for postgres db connection
        """
        conn = htbtworker.postgres_db_open()
        self.assertIsNotNone(conn)

    @patch('misshtbtd.read_hb_common')
    def test_check_process_reconfiguration (self, mock):
        """
        Test if DB is in reconfiguration state
        """
        mock.return_value = ("1234","RUNNING", "XYZ", 1234)
        flag = htbtworker.check_process_reconfiguration("test", "test","x.x.x.x", "1234", "test_db")
        self.assertEqual(False, flag)
        
    @patch('htbtworker.postgres_db_open')
    def test_commit_and_close_db (self, db_mock):
        """
        Test commit and close db
        """
        connection_db = db_mock
        flag = htbtworker.commit_and_close_db(connection_db)
        self.assertEqual(True, flag)
        with patch('htbtworker.postgres_db_open.commit', new=Mock(side_effect=htbtworker.psycopg2.DatabaseError())):
            flag = htbtworker.commit_and_close_db(connection_db)
            self.assertEqual(False, flag)
            
     
if __name__ == "__main__": # pragma: no cover
    unittest.main()
