import os
import sys
import traceback
from os.path import basename
import time

from threading import Thread
import threading
import random
import logging
import json

from client_comm_service import ClientCommService
from bbb_iso_old import BBB_ISO

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
        self.configFileName = None # configured by MAGI
        self.clientID = None #########TODO
        self.scenarioFile = None ##############TODOå

    @agentmethod()
    def initClient(self, msg):
        log.info("Initializing DMM client...")

        self.collection = database.getCollection(self.name)
        self.collection.remove()

        # nodeName: "clietnode-3" --> nodeIndex: 3
        # self.nodeIndex = int(getNodeName().split("-")[1]) 

        globalConfig = None
        with open(self.configFileName, 'r') as configFile:
            globalConfig = json.load(configFile)


        self.CID = unitConfig["CID"] #TODO should be merged
        
        # unitConfig = globalConfig["units"][self.nodeIndex-1]
        # self.unit = DMMUnit(unitConfig)

        nstr=self.clientID #TODo
        splitstr=nstr.split('-')
        self.clientType=splitstr[0]
        self.clientIdx=int(splitstr[1])
        jsonVals=json.load(self.scenarioFile)
        
        sidx=str(self.clientIdx)
        stype=self.clientType
        self.PMax=jsonVals[stype][sidx]["PMax"]
        self.PMin=jsonVals[stype][sidx]["PMin"]
        self.b=jsonVals[stype][sidx]["b"]
        self.c=jsonVals[stype][sidx]["c"]
        self.M=jsonVals[stype][sidx]["M"]
        
        if self.clientType=='G':
            self.delta=jsonVals[stype][sidx]["delta"]
            self.gamma=jsonVals[stype][sidx]["gamma"]
        
        return True

    @agentmethod()
    def registerWithServer(self, msg):
        log.info("Connecting to server...")

        self.comms = ClientCommService()
        self.cthread = self.comms.initAsClient(self.server, self.CID, self.replyHandler)
        # self.cthread = self.comms.initAsClient(toControlPlaneNodeName(self.server), self.CID, self.replyHandler)
        
        payload = self.unit.paramsToDict() #########TODO UNIT DOESN'T EXIST...
        mtype = 'register'
        self.sendMsg(mtype,payload)

        while self.comms.registered is False:
            time.sleep(0.1 + (random.random()*0.3))
        return True
        

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
                
                log.info("Unit updating itself...")
                self.unit.updateE(self.t)
                self.unit.updateAgility(self.t)
                self.unit.updatePForced()
                
                # #Adapt to constraints (change P value when constrained despite no comms)
                # if self.unit.pForced > self.unit.p:
                #     log.info("%s Unit forced to modify its own power, not dispatched enough" % threading.currentThread().name)         
                #     self.unit.setP(self.unit.pForced)

                self.logUnit()
                self.t += 1
                time.sleep(self.unit.tS/10.0)
        except Exception, e:
            log.info("Thread %s threw an exception during main loop" % threading.currentThread().name)
            exc_type, exc_value, exc_tb = sys.exc_info()
            log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        finally:
            self.comms.stop()

    def logUnit(self):
        log.info("%s Logging/Saving unit stats to mongo" % threading.currentThread().name)
        stats = self.unit.__dict__.copy()
        if 'agent' in stats:
            log.info("key 'agent' removed from stats")
            del stats["agent"]
        if 'host' in stats:
            log.info("key 'host' removed from stats")
            del stats["host"]
        if 'created' in stats:
            log.info("key 'created' removed from stats")
            del stats["created"]
        
        stats["CID"] = self.CID
        self.collection.insert(stats)

    def updateUnit(self, t, p):
        log.info("%s updating unit" % threading.currentThread().name)
        self.unit.p = p
        self.unit.updateE(t)
        self.unit.updateAgility(t)
        self.unit.updatePForced()

    def replyHandler(self,CID,msg):
        log.info("%s in reply handler" % threading.currentThread().name)
        log.info("%s Received msg: %s" % (threading.currentThread().name, repr(msg)))

        mtype = msg["type"]
        payload = msg["payload"]

        if mtype == 'dispatch':
            log.info("Received dispatch from server")
            tPMax=self.PMax
            tPMin=self.PMin
            util = self.b+self.c*powerLevel
            util += self.M/((powerLevel-tPMax)**2)-self.M/((powerLevel-tPMin)**2)
            #print clientID + ' b: ' + str(self.b) + ' c: ' + str(self.c) + ' PL: ' + str(powerLevel) + ' u: ' + str(util)

            return util

        elif mtype == 'exit':
            log.info("Exit message received from server")
            self.running = 0
        else:
            log.info("UNKNOWN MESSAGE TYPE RECEIVED")

        # do we want to return E here?

    def sendMsg(self, mtype, payload):
        msg = {}
        msg["type"] = mtype
        msg["payload"] = payload
        self.comms.clientSendValue(msg)

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
        # self.running = 0
        # time.sleep(0.1) # wait for thread to stop
        # self.deRegister()
        # time.sleep(0.1)  # wait for thread to stop
        # self.comms.running = 0
        # return True

def getAgent(**kwargs):
    agent = ISOClientAgent()
    agent.setConfiguration(None, **kwargs)
    return agent
