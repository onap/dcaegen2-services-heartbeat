# Missing Heartbeat service

# Interface Diagram
This repo is the thing in red:

![Alt text](doc/cbs_diagram.png?raw=true)

# Overview

Missing Heartbeat service tracks Heartbeat messages from VNF VMs and generates Missing Heartbeat signal for certain number of failed heartbeats. The service tracks heartbeat Messages from DMaaP message routes and generates Missing Heartbeat signal.  The IP:Port of DMaaP Message router for Input messages and Output messages needs to  be configured. The input and output messages are in JSON format.
The VNF VMs input topic , output topic, periodicity and number of Heartbests can be configuredin cofig YAML file.   
   The format of output messages is still being worked out.
# Assumptions
1. Input and Output messages are in JSON format
2. The periodicity of Heartbeat messages is more than 15sec


# Testing
You need tox:
```
pip install tox
```
Then from the root dir, *not in a virtual env*, just run:
```
tox
```
You may have to alter the tox.ini for the python envs you wish to test with.

