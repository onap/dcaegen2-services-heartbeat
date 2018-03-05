#!/usr/bin/python
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

import requests
import math
import sched, datetime, time
import json
import string
import sys


intvl = 60
missing_htbt = 2
#tracks last epoch time
hearttrack = {}
#tracks sequence number
heartstate = {}
#tracks sequence number differences
heartflag  = {}
#saves heartbeat message for policy
heartmsg   = {}
mr_url = 'http://mrrouter.att.com:3904'
pol_url = 'http://mrrouter.att.com:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'POLICY-HILOTCA-EVENT-OUTPUT'

# Checks for heartbeat event on periodic basis
class PeriodicScheduler(object):                                                  
    def __init__(self):                                                           
        self.scheduler = sched.scheduler(time.time, time.sleep)                   
                                                                            
    def setup(self, interval, action, actionargs=()):                             
        action(*actionargs)                                                       
        self.scheduler.enter(interval, 1, self.setup,                             
                        (interval, action, actionargs))                           
                                                                        
    def run(self):                                                                
        self.scheduler.run()

def get_collector_uri():
    """
    This method waterfalls reads an envioronmental variable called COLLECTOR_HOST
    If that doesn't work, it raises an Exception
    """
    with open('/opt/config/coll_ip.txt', 'r') as myfile:
        coll_ip=myfile.read().replace('\n', '')
        myfile.close()
    with open('/opt/config/coll_port.txt', 'r') as myfile2:
        coll_port=myfile2.read().replace('\n', '')
        myfile2.close()
    if coll_ip and coll_port:
        # WARNING! TODO! Currently the env file does not include the port.
        # But some other people think that the port should be a part of that.
        # For now, I'm hardcoding 8500 until this gets resolved.
        return "http://{0}:{1}".format(coll_ip, coll_port)
    else:
        raise BadEnviornmentENVNotFound("COLLECTOR_HOST")

def get_policy_uri():
    """
    This method waterfalls reads an envioronmental variable called POLICY_HOST
    If that doesn't work, it raises an Exception
    """
    with open('/opt/config/coll_ip.txt', 'r') as myfile:
        pol_ip=myfile.read().replace('\n', '')
        myfile.close()
    with open('/opt/config/coll_port.txt', 'r') as myfile2:
        pol_port=myfile2.read().replace('\n', '')
        myfile2.close()
    if pol_ip and pol_port :
        # WARNING! TODO! Currently the env file does not include the port.
        # But some other people think that the port should be a part of that.
        # For now, I'm hardcoding 8500 until this gets resolved.
        return "http://{0}:{1}".format(pol_ip,pol_port)
    else:
        raise BadEnviornmentENVNotFound("POLICY_HOST")


# Process the heartbeat event on input topic
def periodic_event():  
    print("Checking... ")
    print(datetime.datetime.now())
    #Read heartbeat
    get_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
    print(get_url)
    res = requests.get(get_url)
    #print(res)
    #print(res.headers)
    print(res.text)
    #print(res.json)
    inputString = res.text
    jlist = json.loads(inputString);
    #print("List:"+jlist[0])
    for line in jlist:
       #print(line)
       jobj = json.loads(line)
       #print(jobj)
       srcid = (jobj['event']['commonEventHeader']['sourceId'])
       lastepo = (jobj['event']['commonEventHeader']['lastEpochMicrosec'])
       seqnum = (jobj['event']['commonEventHeader']['sequence'])
       if( srcid in hearttrack ):
         tdiff =  lastepo - hearttrack[srcid]
         sdiff =  seqnum - heartstate[srcid]
         print("Existing source time diff :"+str(tdiff)+" seqdiff :"+str(sdiff))
         # check time difference is within limits and seq num is less than allowed
         if((0 <= tdiff <= 61000000) and sdiff < missing_htbt):
           print("Heartbeat Alive...")
           hearttrack[srcid] = lastepo
           heartstate[srcid] = seqnum;
           heartflag[srcid]  = sdiff;
           heartmsg[srcid]  = jobj;
         else:
           print("Heartbeat Dead raising alarm event")
           #payload = {'Event': 'Heartbeat Failure', 'Host': srcid, 'LastTimestamp': hearttrack[srcid], 'Sequence': heartstate[srcid]}
           payload = {"event": {
                                "commonEventHeader": {
                                                "reportingEntityName": "VNFVM",
                                                "reportingEntityName": "VNFVM",
                                                "startEpochMicrosec": 1508641592248000,
                                                "lastEpochMicrosec": 1508641592248000,
                                                "eventId": "VNFVM_heartbeat",
                                                "sequence": 1,
                                                "priority": "Normal",
                                                "sourceName": "VNFVM",
                                                "domain": "heartbeat",
                                                "eventName": "Heartbeat_Vnf",
                                                "internalHeaderFields": {
                                                                "closedLoopFlag": "True",
                                                                "eventTag": "hp.Heartbeat Service.20171022.8447964515",
                                                                "collectorTimeStamp": "Sun, 10 22 2017 03:04:27 GMT",
                                                                "lastDatetime": "Sun, 22 Oct 2017 03:06:32 +0000",
                                                                "closedLoopControlName": "ControlLoopEvent1",
                                                                "firstDatetime": "Sun, 22 Oct 2017 03:06:32 +0000"
                                                },
                                                "reportingEntityId": "cff8656d-0b42-4eda-ab5d-3d2b7f2d74c8",
                                                "version": 3,
                                                "sourceId": "cff8656d-0b42-4eda-ab5d-3d2b7f2d74c8"
                                 }
                            }
                       }
           payload = heartmsg[srcid]
           print(payload)
           send_url = pol_url+'/events/'+outopic+'/DefaultGroup/1?timeout=15000'
           print(send_url)
           #Send response for policy on output topic
           r = requests.post(send_url, data=payload)
           print(r.status_code, r.reason)
           del heartstate[srcid]
           del hearttrack[srcid]
           del heartflag[srcid]
       else:
         print("Adding new source")
         hearttrack[srcid] = lastepo
         heartstate[srcid] = seqnum
         heartflag[srcid] = 1
         heartmsg[srcid]  = jobj;
    chkeys = []
    for key in heartstate.iterkeys():
       print(key,heartstate[key])
       if( heartflag[key] == 0 ):
          print("Heartbeat Dead raise alarm event"+key)
          chkeys.append( key )
          #payload = {'Event': 'Heartbeat Failure', 'Host': key, 'LastTimestamp': hearttrack[key], 'Sequence': heartstate[key]}
          #print payload
          payload = {"event": {
                                "commonEventHeader": {
                                                "reportingEntityName": "VNFVM",
                                                "startEpochMicrosec": 1508641592248000,
                                                "lastEpochMicrosec": 1508641592248000,
                                                "eventId": "VNFVM_heartbeat",
                                                "sequence": 1,
                                                "priority": "Normal",
                                                "sourceName": "VNFVM",
                                                "domain": "heartbeat",
                                                "eventName": "Heartbeat_Vnf",
                                                "internalHeaderFields": {
                                                                "closedLoopFlag": "True",
                                                                "eventTag": "hp.Heartbeat Service.20171022.8447964515",
                                                                "collectorTimeStamp": "Sun, 10 22 2017 03:04:27 GMT",
                                                                "lastDatetime": "Sun, 22 Oct 2017 03:06:32 +0000",
                                                                "closedLoopControlName": "ControlLoopEvent1",
                                                                "firstDatetime": "Sun, 22 Oct 2017 03:06:32 +0000"
                                                },
                                                "reportingEntityId": "cff8656d-0b42-4eda-ab5d-3d2b7f2d74c8",
                                                "version": 3,
                                                "sourceId": "cff8656d-0b42-4eda-ab5d-3d2b7f2d74c8"
                                 }
                            }
                       }
          payload = heartmsg[key]
          print(payload)
          send_url = pol_url+'/events/'+outopic+'/DefaultGroup/1?timeout=15000'
          print(send_url)
          r = requests.post(send_url, data=payload)
          print(r.status_code, r.reason)
       heartflag[key] = 0
    for chkey in chkeys:
       print(chkey)
       del heartstate[chkey]
       del hearttrack[chkey]
       del heartflag[chkey]

total = len(sys.argv)
cmdargs = str(sys.argv)
print ("The total numbers of args passed to the script: %d " % total)
print ("Args list: %s " % cmdargs)
print ("Script name: %s" % str(sys.argv[0]))
for i in range(total):
    print ("Argument # %d : %s" % (i, str(sys.argv[i])))
if( total >= 6 ):
  mr_url = get_collector_uri()
  pol_url = get_policy_uri()
  #mr_url = sys.argv[1]
  missing_htbt = float(int(sys.argv[2]))
  intvl = float(int(sys.argv[3]))
  intopic = sys.argv[4]
  outopic = sys.argv[5]
print ("Interval %s " % intvl)
#intvl = 60 # every second  
periodic_scheduler = PeriodicScheduler()  
periodic_scheduler.setup(intvl, periodic_event) # it executes the event just once  
periodic_scheduler.run() # it starts the scheduler  
