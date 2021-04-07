# ============LICENSE_START=======================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2021 Samsung Electronics. All rights reserved.
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

import os
import string
import sys
import setuptools
from setuptools import setup, find_packages

## #from pip.req import parse_requirements
## try: # for pip >= 10
##     from pip._internal.req import parse_requirements
## except ImportError: # for pip <= 9.0.3
##     from pip.req import parse_requirements
## #from pip.download import PipSession
## try: # for pip >= 10
##     from pip._internal.download import PipSession
## except ImportError: # for pip <= 9.0.3
##     from pip.download import PipSession

setup(
    name='miss_htbt_service',
    description='Missing heartbeat microservice to communicate with policy-engine',
    version='2.1.1',
    #packages=find_packages(exclude=["tests.*", "tests"]),
    packages=find_packages(),
    install_requires=[
"requests==2.23.0",
"onap_dcae_cbs_docker_client==1.0.1",
"six==1.15.0",
"PyYAML==5.4",
"httplib2==0.19.0",
"HTTPretty==1.0.5",
"pyOpenSSL==20.0.1",
"Wheel==0.36.2",
"psycopg2-binary==2.8.6"
    ],
    author = "Vijay Venkatesh Kumar",
    author_email = "vv770d@att.com",
    license = "",
    keywords = "missing heartbeat microservice",
    url = "https://gerrit.onap.org/r/#/admin/projects/dcaegen2/platform/heartbeat",
    zip_safe=False,
)
