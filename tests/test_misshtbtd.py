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
import misshtbtd
import time
import psycopg2
import os
import tempfile
import json 
import unittest
from unittest.mock import *
from _pytest.outcomes import skip
from pickle import FALSE

class Test_misshtbtd(unittest.TestCase):

    def setUp(self):
        htbtworker.configjsonfile = (os.path.dirname(__file__))+"/test-config.json"

    @patch ('psycopg2.connect')
    def test_create_database(self, mock1):
        status = True
        mock_cursor = MagicMock()        
        mock_cursor.configure_mock(
            **{
                "fetchone.return_value": [("1")]
            }
        )
        mock1.return_value =  mock_cursor
        misshtbtd.create_database("vnf_table_1",htbtworker.configjsonfile, "10.0.0.0","1234","testuser","testpwd","heartbeatdb")
        self.assertEqual(status, True)
    
    @patch ('htbtworker.postgres_db_open')
    def test_read_hb_common(self, mock1):
        
        mock_cursor = Mock()        
        mock_cursor.configure_mock(
            **{
                "cursor.return_value.fetchall.return_value": [["1", "AA", "123456789", "RUNNING"]]
            }
        )
        mock1.return_value = mock_cursor
        self.assertEqual(('1', 'RUNNING', 'AA', '123456789'),  misshtbtd.read_hb_common("testuser","testpwd","10.0.0.0","1234","heartbeatdb"))

    @patch ('misshtbtd.db_table_creation_check')
    @patch ('htbtworker.postgres_db_open')
    def test_create_update_hb_common(self, mock1, mock2):
        '''
        TODO: argument ordering TBD
        '''
        mock_cursor = Mock()      
        mock1.return_value = mock_cursor  
        mock2.return_value = True
        status = True
        misshtbtd.create_update_hb_common (0,111, "RUNNING", "testuser","testpwd","10.0.0.0","1234","testdb")
        self.assertEqual(status, True)
        mock2.return_value = False
        misshtbtd.create_update_hb_common (1,111, "RUNNING", "testuser","testpwd","10.0.0.0","1234","testdb")
        self.assertEqual(status, True)

    def test_db_table_creation_check (self):
        """
        Test to verify existence of given table
        """
        mock_cursor = Mock()        
        mock_cursor.configure_mock(
            **{
                "cursor.return_value.fetchone.return_value": ("vnf_table_2")
            }
        )
        status = misshtbtd.db_table_creation_check (mock_cursor,"vnf_table_2")
        self.assertEqual(status, True)        

    @patch ('misshtbtd.db_table_creation_check')
    def test_create_update_vnf_table_1 (self, mock1):
        """
        TBD
        """
        status = True
        mock_cursor = Mock()        
        mock_cursor.configure_mock(
            **{
                "cursor.return_value.fetchall.return_value": [["Heartbeat_vDNS"],["Heartbeat_vFW"]]
            }
        )
        misshtbtd.create_update_vnf_table_1 (htbtworker.configjsonfile,1, mock_cursor)
        self.assertEqual(status, True) 
        misshtbtd.create_update_vnf_table_1 (htbtworker.configjsonfile,0, mock_cursor)
        self.assertEqual(status, True) 

    def test_read_hb_properties_default_from_file (self):
        """
        TBD
        """
        return_val = ("10.0.0.0","1234", "postgres-test", "postgres-test", "postgres", "True", "300")
        misshtbtd.hb_properties_file = (os.path.dirname(__file__)) + "/hbproperties-test.yaml"
        (ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) = misshtbtd.read_hb_properties_default()
        self.assertEqual (return_val,(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) )

    @patch.dict(os.environ, {"pg_ipAddress": "10.0.0.10", "pg_portNum":"1234", "pg_userName": "test","pg_passwd":"test"})
    def test_read_hb_properties_default_from_env (self):
        """
        TBD
        """
        return_val = ("10.0.0.10","1234", "test", "test", "postgres", "True", "300")
        misshtbtd.hb_properties_file = (os.path.dirname(__file__)) + "/hbproperties-test.yaml"
        (ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) = misshtbtd.read_hb_properties_default()
        self.assertEqual (return_val,(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) )

    def test_read_hb_properties_from_file (self):
        """
        TBD
        """
        htbtworker.configjsonfile = (os.path.dirname(__file__))+"/test-config.json"
        misshtbtd.hb_properties_file = (os.path.dirname(__file__)) + "/hbproperties-test.yaml"
        
        return_val = ("10.0.4.1","5432", "postgres", "postgres", "postgres", "True", "300")
        (ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) = misshtbtd.read_hb_properties(htbtworker.configjsonfile)
        self.assertEqual (return_val,(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) )

    @patch.dict(os.environ, {"pg_ipAddress": "10.0.0.10", "pg_portNum":"1234", "pg_userName": "test","pg_passwd":"test"})
    def test_read_hb_properties_exception_handling (self):
        """
        TBD
        """
        htbtworker.configjsonfile = (os.path.dirname(__file__))+"/aa-config.json"
        misshtbtd.hb_properties_file = (os.path.dirname(__file__)) + "/hbproperties-test.yaml"
        
        return_val = ("10.0.0.10","1234", "test", "test", "postgres", "True", "300")
        (ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) = misshtbtd.read_hb_properties(htbtworker.configjsonfile)
        self.assertEqual (return_val,(ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval) )


    @patch ('mod.trapd_get_cbs_config')
    def test_fetch_json_file (self, mock1):
        """
        TBD
        """
        #mock.return_value.is_file.return_value = True
        mock1.return_value = True
        misshtbtd.CONFIG_PATH = "test-config.json"
        filename = misshtbtd.fetch_json_file()
        self.assertEqual (misshtbtd.CONFIG_PATH, filename)
        # mock1.return_value = False
        # filename = misshtbtd.fetch_json_file()
        # self.assertEqual ("./etc/config.json", filename)

    @patch ('htbtworker.postgres_db_open')
    @patch ('misshtbtd.db_table_creation_check')
    @patch ('misshtbtd.create_update_vnf_table_1')
    def test_create_update_db(self, mock1, mock2, mock3):
        '''
        TODO: argument ordering TBD
        '''
        mock_cursor = Mock()      
        mock3.return_value = mock_cursor  
        mock1.return_value = True
        mock2.return_value = True
        status = True
        misshtbtd.create_update_db (0,htbtworker.configjsonfile, "10.0.0.0", "1234", "test","test", "testdb")
        self.assertEqual(status, True)
        mock1.return_value = False
        misshtbtd.create_update_db (0,htbtworker.configjsonfile, "10.0.0.0", "1234", "test","test", "testdb")
        self.assertEqual(status, True)

    @patch ('multiprocessing.Process')
    @patch ('misshtbtd.create_update_db')
    @patch('misshtbtd.create_update_hb_common')
    def test_create_process(self, mock1, mock2, mock3):
        job_list = []
        mock_process = Mock()
        mock_process.configure_mock(
            **{
                "start.return_value": "1"
            }
        )
        mock1.return_value = mock_process
        job_list = misshtbtd.create_process ([],htbtworker.configjsonfile, 1)
        self.assertTrue(job_list)

    @patch ('multiprocessing.Process')
    @patch ('misshtbtd.read_hb_common')
    @patch ('misshtbtd.create_update_db')
    @patch ('misshtbtd.create_update_hb_common')
    def test_main(self, mock1, mock2, mock3, mock4):
        status = True
        mock_process = Mock()
        mock_process.configure_mock(
            **{
                "start.return_value": "1",
                "pid.return_Value":"1111"
            }
        )
        mock1.return_value = mock_process
        current_time = round(time.time())
        mock2.return_value = ('1', 'RUNNING', 'AA', current_time)
        misshtbtd.main()
        self.assertEqual(status, True)

if __name__ == "__main__": # pragma: no cover
    unittest.main()
