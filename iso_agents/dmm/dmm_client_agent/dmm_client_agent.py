import os
import sys
import traceback
import time

from threading import Thread
import threading
import random
import logging
import json

from client_comm_service import ClientCommService
from magi.util import database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.util.config import getNodeName
from magi.util.helpers import toControlPlaneNodeName
import numpy as np

log = logging.getLogger(__name__)

class DMMClientAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.server = None # configured by MAGI
        self.configPath = None # configured by MAGI
        self.clientID = None #########TODO

    @agentmethod()
    def initClient(self, msg):
        log.info("Initializing DMM client...")

        self.collection = database.getCollection(self.name)
        self.collection.remove()

        nodeAssignment = None
        with open(os.path.join(self.configPath, "nodeAssignment.json"), 'r') as assignmentFile:
            nodeAssignment = json.load(assignmentFile)

        # nodeName: "clietnode-3" --> nodeIndex: 3
        self.nodeIndex = int(getNodeName().split("-")[1]) 
        # clientId ==> maps int nodeIndex to string like "DC-8"
        self.clientID = nodeAssignment[nodeIndex]
        
        nstr = self.clientID
        splitstr = nstr.split('-')
        self.clientType = splitstr[0]
        self.clientIdx = int(splitstr[1])

        jsonVals = json.load(os.path.join(self.configPath, "fullcase.json"))
        
        sidx = str(self.clientIdx)
        stype = self.clientType
        self.PMax = jsonVals[stype][sidx]["PMax"]
        self.PMin = jsonVals[stype][sidx]["PMin"]
        self.b = jsonVals[stype][sidx]["b"]
        self.c = jsonVals[stype][sidx]["c"]
        self.M = jsonVals[stype][sidx]["M"]
        
        if self.clientType=='G':
            self.delta=jsonVals[stype][sidx]["delta"]
            self.gamma=jsonVals[stype][sidx]["gamma"]
        
        return True

    # no longer explicity registers with server, just connects
    @agentmethod() 
    def registerWithServer(self, msg):
        log.info("Connecting to server...")

        self.commService = ClientCommService()
        self.commThread = self.commService.startClient(self.server, self.clientID, self.replyHandler)
        
        while self.commService.connected is False:
            time.sleep(0.1 + (random.random()*0.3))
        return True
    
    def replyHandler(self, clientID, msg):
        threadName = threading.currentThread().name
        log.info("%s in reply handler" % threadName)
        log.info("%s Received msg: %s" % (threadName, repr(msg)))

        mtype = msg["type"]
        payload = msg["payload"]

        if mtype == 'dispatch':
            log.info("Thread %s: Received dispatch from server" % threadName)
            
            powerLevel = payload["powerLevel"] #confirm todo
            
            tPMax = self.PMax
            tPMin = self.PMin
            util = self.b + self.c * powerLevel
            util += self.M/((powerLevel-tPMax)**2)-self.M/((powerLevel-tPMin)**2)

            return util

        elif mtype == 'exit':
            log.info("Thread %s: Exit message received from server" % threadName)
            self.running = 0
        else:
            log.info("Thread %s: UNKNOWN MESSAGE TYPE RECEIVED" % threadName)


    @agentmethod()
    def startClient(self, msg):
        log.info("Starting client's simulation...")
        self.running = 1
        self.runClient()
        return True

    def runClient(self):
        try:
            while self.running:
                log.info("%s Running" % threading.currentThread().name)
                self.logUnit()
                time.sleep(0.1)
        except Exception, e:
            log.info("Thread %s threw an exception during main loop" % threading.currentThread().name)
            exc_type, exc_value, exc_tb = sys.exc_info()
            log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        finally:
            self.commService.stop()

    def logUnit(self):
        log.info("%s Logging/Saving unit stats to mongo" % threading.currentThread().name)
        # maybe store other vals too
        stats = {
            "PMax": self.PMax,
            "PMin": self.PMin,
            "b": self.b,
            "c": self.c,
            "M": self.M,
            "clientID": self.clientID
        }
        self.collection.insert(stats)

    def sendMsg(self, mtype, payload):
        msg = {}
        msg["type"] = mtype
        msg["payload"] = payload
        self.commService.sendValue(msg)

    def sendParams(self):
        payload=self.unit.paramsToDict()
        mtype='setParam'
        self.sendMsg(mtype,payload)
        
    def deRegister(self):
        payload='null'
        mtype='deregister'
        self.sendMsg(mtype,payload)
        
    @agentmethod()
    def stopClient(self, msg):
        """ No longer being used..."""
        log.info("Shutting client down...")

def getAgent(**kwargs):
    agent = ISOClientAgent()
    agent.setConfiguration(None, **kwargs)
    return agent
