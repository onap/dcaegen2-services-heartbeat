#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2023 AT&T Intellectual Property. All rights reserved.
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

import db_monitoring
import htbtworker
import logging
import requests
import tempfile
import os
import json
import unittest

from unittest.mock import *
from _pytest.outcomes import skip

_logger = logging.getLogger(__name__)


class Test_db_monitoring(unittest.TestCase):
    def setUp(self):
        htbtworker.configjsonfile = (os.path.dirname(__file__)) + "/test-config.json"

    @patch("requests.post")
    def test_sendControlLoopEvent(self, mock1):
        status = True
        mock_resp = Mock()
        mock_resp.configure_mock(**{"status_code": 200})
        mock1.return_value = mock_resp
        db_monitoring.sendControlLoopEvent(
            "ONSET", "ABC", "1.0", "vFW", "vFW", "VNF", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ONSET", "ABC", "1.0", "vFW", "vFW", "VM", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ABATED", "ABC", "1.0", "vFW", "vFW", "VNF", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ABATED", "ABC", "1.0", "vFW", "vFW", "VM", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)

    @patch("misshtbtd.read_hb_common", return_value=("1234", "RUNNING", "XYZ", 1234))
    @patch("htbtworker.postgres_db_open")
    def test_db_monitoring(self, mock1, mock2):
        status = True
        mock_cursor = Mock()
        mock2.cursor.return_value = mock_cursor
        db_monitoring.db_monitoring(
            "111", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)
        db_monitoring.db_monitoring(
            "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)
        mock1.cursor.return_value = ("1234", "RECONFIGURATION", "XYZ", 1234)
        db_monitoring.db_monitoring(
            "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)

    def test_db_monitoring_wrapper(self):
        status = True
        db_monitoring.db_monitoring_wrapper("111", htbtworker.configjsonfile, number_of_iterations=0)
        self.assertEqual(status, True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
