import os
import sys
import traceback
from os.path import basename
import time

from threading import Thread
import threading
import random
import logging
import simplejson as json

from client_comm_service import ClientCommService
from bbb_iso import BBB_ISO

from magi.util import database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.util.config import getNodeName

log = logging.getLogger(__name__)

class ISOClientAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.server = None # must be configured by MAGI
        self.configFileName = None # must be configured by MAGI

    @agentmethod()
    def initClient(self, msg):
        log.info("Initializing client...")

        self.collection = database.getCollection(self.name)
        self.collection.remove()
        
        # nodeName: "clietnode-3" --> nodeIndex: 3
        self.nodeIndex = int(getNodeName().split("-")[1]) 

        globalConfig = None
        with open(self.configFileName, 'r') as configFile:
            globalConfig = json.load(configFile)

        unitConfig = globalConfig["units"][self.nodeIndex-1]

        self.CID = unitConfig["CID"]
        self.unit = BBB_ISO.dictToUnit(unitConfig)
        self.unit.tS = globalConfig["timeStep"]
        self.t = 0

    @agentmethod()
    def registerWithServer(self, msg):
        log.info("Connecting to server...")
        self.comms = ClientCommService()
        self.cthread = self.comms.initAsClient(self.server, self.CID, self.replyHandler)
        self.sendRegister()
        while self.comms.registered is False:
            time.sleep(0.01)
        return True
        
    @agentmethod()
    def startClient(self, msg):
        log.info("Starting client's simulation...")
        self.running = 1
        self.runClient()
        return True

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

    def runClient(self):
        try:
            while self.running:
                log.info("%s Running" % threading.currentThread().name)
                time.sleep(self.unit.tS/10.0)
                #Adapt to constraints (change P value when constrained despite no comms)
                if self.unit.pForced > self.unit.p:
                    log.info("%s Unit forced to modify its own power, not dispatched enough" % threading.currentThread().name)
                    # TODO: need to notify server of this
                    self.t += 1 # think about this...
                    self.updateUnit(self.t, self.unit.pForced)

                self.logUnit()            
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
            log.info("AGENT IN STATS")
            del stats["agent"]
        if 'host' in stats:
            log.info("HOST IN STATS")
            del stats["host"]
        if 'created' in stats:
            log.info("'created' in stats:")
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
            newTime = payload["currentTime"]
            log.info("%s Updating Unit params based on dispatch" % threading.currentThread().name)
            self.updateUnit(newTime, payload["p"])
            self.t = newTime
            # self.sendEnergy() 
            # self.sendParams()
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
        
    def sendEnergy(self):
        payload={}
        payload["e"]=self.unit.e
        mtype='setEnergy'
        self.sendMsg(mtype,payload)

    def sendRegister(self):
        log.info("Registering with server!")
        payload = self.unit.paramsToDict()
        mtype = 'register'
        self.sendMsg(mtype,payload)

    def deRegister(self):
        payload='null'
        mtype='deregister'
        self.sendMsg(mtype,payload)
        

def getAgent(**kwargs):
    agent = ISOClientAgent()
    agent.setConfiguration(None, **kwargs)
    return agent


'''
blankMsg={}
blankMsg['type']='pass'
blankMsg['payload']='none'
return blankMsg
'''