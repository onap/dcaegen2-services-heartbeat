# ============LICENSE_START=======================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
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
# ECOMP is a trademark and service mark of AT&T Intellectual Property.

import os
import string
import sys
import setuptools
from setuptools import setup, find_packages

#from pip.req import parse_requirements
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements
#from pip.download import PipSession
try: # for pip >= 10
    from pip._internal.download import PipSession
except ImportError: # for pip <= 9.0.3
    from pip.download import PipSession

setup(
    name='miss_htbt_service',
    description='Missing heartbeat microservice to communicate with policy-engine',
    version='2.1.0',
    #packages=find_packages(exclude=["tests.*", "tests"]),
    packages=find_packages(),
    install_requires=[
"request==1.0.1",
"requests==2.18.3",
"onap_dcae_cbs_docker_client==1.0.1",
"six==1.10.0",
"PyYAML==3.12",
"httplib2==0.9.2",
"HTTPretty==0.8.14",
"pyOpenSSL==17.5.0",
"Wheel==0.31.0"
    ],
    author = "Vijay Venkatesh Kumar",
    author_email = "vv770d@att.com",
    license = "",
    keywords = "missing heartbeat microservice",
    url = "https://gerrit.onap.org/r/#/admin/projects/dcaegen2/platform/heartbeat",
    zip_safe=False,
)
