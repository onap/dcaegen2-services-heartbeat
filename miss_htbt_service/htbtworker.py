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
#  Author  Gokul Singaraju gs244f@att.com
#    Simple Microservice
#    Tracks Heartbeat messages on input topic in DMaaP
#    and generates Missing Heartbeat signal for Policy Engine

import requests
import math
import sched, datetime, time
import json
import string
import sys


# Initialise tracking hash tables
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
mr_url = 'http://mrrouter.onap.org:3904'
pol_url = 'http://mrrouter.onap.org:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'POLICY-HILOTCA-EVENT-OUTPUT'
nfc = "vVNF"
cl_loop = 'ControlLoopEvent1'
periodic_scheduler = None

# Checks for heartbeat event on periodic basis
class PeriodicScheduler(object):                                                  
    def __init__(self):                                                           
        self.scheduler = sched.scheduler(time.time, time.sleep)                   
                                                                            
    def setup(self, interval, action, actionargs=()):                             
        #print("Args are :", locals())
        action(*actionargs)                                                       
        self.scheduler.enter(interval, 1, self.setup,(interval, action, actionargs))                           
    def run(self): 
        self.scheduler.run()

    def stop(self):
        list(map(self.scheduler.cancel, self.scheduler.queue))


# Process the heartbeat event on input topic
def periodic_event():  
   global periodic_scheduler
   global mr_url, pol_url, missing_htbt, intvl, intopic, outopic, nfc, cl_loop
   ret = 0
   #print("Args are :", locals())
   print("{0} Checking...".format(datetime.datetime.now()))
   #Read heartbeat
   #get_url = mr_url+'/events/'+intopic+'/DefaultGroup/1?timeout=15000'
   get_url = mr_url+'/DefaultGroup/1?timeout=15000'
   print("Getting :"+get_url)
   try:
    res = requests.get(get_url)
    #print(res)
    #print(res.headers)
    print(res.text)
    #print(res.json)
    inputString = res.text
    #jlist = json.loads(inputString)
    jlist = inputString.split('\n');
    #print("List:"+jlist[0])
    # Process the DMaaP input message retreived
    for line in jlist:
       print("Line:"+line)
       jobj = json.loads(line)
       #print(jobj)
       if( nfc != jobj['event']['commonEventHeader']['nfNamingCode']) :
             continue
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
           jobj["internalHeaderFields"] = json.dumps({
                                                       "closedLoopFlag": "True",
                                                       "eventTag": "hp.Heartbeat Service.20171022.8447964515",
                                                       "collectorTimeStamp": "Sun, 10 22 2017 03:04:27 GMT",
                                                       "lastDatetime": "Sun, 22 Oct 2017 03:06:32 +0000",
                                                       "closedLoopControlName": cl_loop,
                                                       "firstDatetime": "Sun, 22 Oct 2017 03:06:32 +0000"
                                                });
           heartmsg[srcid]  = jobj;
           payload = heartmsg[srcid]
           print(payload)
           #psend_url = pol_url+'/events/'+outopic+'/DefaultGroup/1?timeout=15000'
           psend_url = pol_url+'/DefaultGroup/1?timeout=15000'
           print(psend_url)
           print("Heartbeat Dead raising alarm event "+psend_url)
           #Send response for policy on output topic
           r = requests.post(psend_url, data=payload)
           print(r.status_code, r.reason)
           ret = r.status_code
           del heartstate[srcid]
           del hearttrack[srcid]
           del heartflag[srcid]
       else:
         print("Adding new source")
         hearttrack[srcid] = lastepo
         heartstate[srcid] = seqnum
         heartflag[srcid] = 1
         heartmsg[srcid]  = jobj;
         ret = 1
    chkeys = []
    for key in heartstate.keys():
       print(key,heartstate[key])
       if( heartflag[key] == 0 ):
          print("Heartbeat Dead raise alarm event"+key)
          chkeys.append( key )
          #print payload
          heartmsg[key]["internalHeaderFields"] = json.dumps({
                                      "closedLoopFlag": "True",
                                      "eventTag": "hp.Heartbeat Service.20171022.8447964515",
                                      "collectorTimeStamp": "Sun, 10 22 2017 03:04:27 GMT",
                                      "lastDatetime": "Sun, 22 Oct 2017 03:06:32 +0000",
                                      "closedLoopControlName": cl_loop,
                                      "firstDatetime": "Sun, 22 Oct 2017 03:06:32 +0000"
                                 })
          payload = heartmsg[key]
          print(payload)
          send_url = pol_url+'/DefaultGroup/1?timeout=15000'
          print(send_url)
          r = requests.post(send_url, data=payload)
          print(r.status_code, r.reason)
          ret = r.status_code
       heartflag[key] = 0
    for chkey in chkeys:
       print(chkey)
       del heartstate[chkey]
       del hearttrack[chkey]
       del heartflag[chkey]
   except requests.exceptions.ConnectionError:
      print("Connection refused ..")
   return ret

#test setup for coverage
def test_setup(args):
    global mr_url, pol_url, missing_htbt, intvl, intopic, outopic
    missing_htbt = float(int(args[2]))
    intvl = float(int(args[3]))
    intopic = args[4]
    outopic = args[5]
    mr_url = get_collector_uri()+'/events/'+intopic
    pol_url = get_policy_uri()+'/events/'+outopic
    print ("Message router url %s " % mr_url)
    print ("Policy url %s " % pol_url)
    print ("Interval %s " % intvl)
    print ("Input topic %s " % intopic)
    print ("Output topic %s " % outopic)
    #intvl = 60 # every second  

#Main invocation
def main(args):
    global periodic_scheduler
    global mr_url, pol_url, missing_htbt, intvl, intopic, outopic, nfc, cl_loop
    #mr_url = get_collector_uri()
    #pol_url = get_policy_uri()
    mr_url = args[0]
    intopic = args[1]
    pol_url = args[2]
    outopic = args[3]
    nfc = args[4]
    missing_htbt = int(args[5])
    intvl = int(args[6])
    cl_loop = args[7]
    print ("Message router url %s " % mr_url)
    print ("Policy router url %s " % pol_url)
    print ("Interval %s " % intvl)
    if( cl_loop != "internal_test") :
      #intvl = 60 # every second  
      #Start periodic scheduler runs every interval
      periodic_scheduler = PeriodicScheduler() 
      periodic_scheduler.setup(intvl, periodic_event,) # it executes the event just once  
      periodic_scheduler.run() # it starts the scheduler  

if __name__ == "__main__":
  total = len(sys.argv)
  cmdargs = str(sys.argv)
  print ("The total numbers of args passed to the script: %d " % total)
  print ("Missing Heartbeat Args list: %s " % cmdargs)
  print ("Script name: %s" % str(sys.argv[0]))
  for i in range(total):
    print ("Argument # %d : %s" % (i, str(sys.argv[i])))
  main(sys.argv[1:])


#force stop scheduler
def stop():
  global periodic_scheduler
  if not periodic_scheduler is None:
     periodic_scheduler.stop()
