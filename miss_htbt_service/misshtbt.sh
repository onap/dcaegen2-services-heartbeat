#!/bin/sh
#
# ============LICENSE_START=======================================================
# org.onap.dcae
# ================================================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
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

# get to where we are supposed to be for startup
cd /app/bin || (echo "Failed to cd to /app/bin" && exit 1)

# set location of SSL certificates
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-bundle.crt

# PYTHONUNBUFFERED:
#    set PYTHONUNBUFFERED to a non-empty string to avoid output buffering;
#    comment out for runtime environments/better performance!
# export PYTHONUNBUFFERED="True"

# set location of config broker server overrride IF NEEDED
#
#export CBS_HTBT_JSON=../etc/config.json

# want tracing?  Use this:
# python3 -m trace --trackcalls misshtbtd.py -v

# want verbose logging?  Use this:
# misshtbtd.py -v

# standard startup?  Use this:
# misshtbtd.py

# unbuffered io for logs and verbose logging? Use this:
python3 -u misshtbtd.py -v

