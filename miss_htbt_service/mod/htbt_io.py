# ============LICENSE_START=======================================================)
# Copyright (c) 2018-2023 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright (c) 2020 Deutsche Telekom. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================

"""
"""

__docformat__ = "restructuredtext"

# basics
import datetime
import os

prog_name = os.path.basename(__file__)

# # # # # # # # # # # # #
# fx: stdout_logger
# # # # # # # # # # # # #


def stdout_logger(_msg):
    """
    Log info/errors to stdout.  This is done:
      - for critical runtime issues

    :Parameters:
      _msg
         message to print
    :Exceptions:
      none
    :Keywords:
      log stdout
    :Variables:
    """

    t_out = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S,%f")[:-3]

    print("%s %s" % (t_out, _msg))
