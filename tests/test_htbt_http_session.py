# ============LICENSE_START=======================================================
# Copyright (c) 2017-2022 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
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

import unittest
from miss_htbt_service.mod import htbt_http_session


class test_init_session_obj(unittest.TestCase):
    """
    Test the init_session_obj mod
    """

    def test_correct_usage(self):
        """
        Test that attempt to create http session object works
        """
        result = htbt_http_session.init_session_obj()
        compare = str(result).startswith("<requests.sessions.Session object at")
        self.assertEqual(compare, True)
