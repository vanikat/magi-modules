import sys
import traceback
from os.path import basename
import threading
import random
import time
import json

from server_comm_service import ServerCommService
from bbb_iso import BBB_ISO
from magi.util import database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

import logging
log = logging.getLogger(__name__)

import os
import io

class ISOServerAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.simRunning = False
        self.configFileName = None # must be configured by MAGI

    @agentmethod()
    def initServer(self, msg):
        log.info("Initializing ISOServer...")
        
        globalConfig = None
        log.info("Attempting to read from configFile: %s" % self.configFileName)
        with open(self.configFileName, 'r') as configFile:
            globalConfig = json.load(configFile)

        self.tS = globalConfig["timeStep"]
        self.numIterations = globalConfig["numIterations"]
        self.ISO = BBB_ISO()
        self.VPP = globalConfig["vpp"]
        self.CIDList = {}
        
        self.collection = database.getCollection(self.name)
        self.collection.remove()
        
        self.comms = ServerCommService()
        self.comms.initAsServer(self.replyHandler)


        self.DISO=DMM_ISO(self.dmmCaseFile,self.caseNum,1,0.1,0.1,2,0.001)
        self.clientList=self.DISO.getClientList()
        
        self.running=1
        self.lastUpdate=0
        self.lastUpdateList={}
        for key,val in self.clientList.iteritems():
            self.lastUpdateList[key]=self.lastUpdate
        nthread=Thread(name='isoServerThread',target=self.serverThread)
        #Block until all clients connected
        while len(self.comms.slock) < len(self.clientList):
            pass
        nthread.start()
        
        return True

    @agentmethod()
    def startSimulation(self, msg):
        log.info("Starting simulation...")
        self.simRunning = True
        self.simThread = threading.Thread(target=self.runServer)
        self.simThread.start()
        return True
    
    def runServer(self):
        log.info( "RunServer started... ########")

        try:
            log.info("CIDList len: %d" % len(self.CIDList))
            log.info("ISO.unitList len: %s" % len(self.ISO.unitList))
            time.sleep(self.tS) # let all clients connect and get ready

            for t in range(1, self.numIterations + 1):
                if self.simRunning:
                    log.info("Simulation Timestep %d..." % t)
                    time.sleep(self.tS/10.0)
                    pDispatch = self.VPP[t]
                    log.info("AgileBalancing %d units of power..." % pDispatch)
                    self.ISO.agileBalancing(t,pDispatch)
                    
                    log.info("Sending dispatch to all units...")
                    self.sendAllDispatch()
                    
                    log.info("Logging current state...")
                    stats = self.ISO.generateStats(t, pDispatch)
                    self.collection.insert(stats)
                    
                    agilityStats = self.ISO.generateAgilityStats(t)
                    self.collection.insert(agilityStats)

                    pStats = self.ISO.generatePStats(t)
                    self.collection.insert(pStats)
                    
                else:
                    log.info( "Simulation has been told to exit, timestep = %d" % t)
                    break
        except Exception, e:
            log.info("RunServer threw an exception during main loop")
            exc_type, exc_value, exc_tb = sys.exc_info()
            log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        finally:
            self.sendAllExitMsg()
            self.comms.stop()

        log.info("RunServer ending...")

    @agentmethod()
    def stopSimulation(self, msg):
        """No longer used"""
        log.info("Stopping simulation...")
        self.simRunning = False
        self.comms.stop()
        return True

    def replyHandler(self, CID, msg):
        # log.info("REPLYHANDLER: CID: %s, msg: %s" % (CID, msg))
        #Messages from clients 
        #msg is dictionary from json extraction, dictionary must have type then payload (potentially another dictionary)
        mtype = msg["type"]
        mdata = msg["payload"]
        if mtype == 'register': 
            self.ISO.registerClient(CID, mdata)
            self.CIDList[CID] = True
            log.info("Client %s registered." % str(CID))
        elif mtype == 'deregister':
            self.ISO.deregisterClient(CID)
            del self.CIDList[CID]
            log.info("Client %s de-registered." % str(CID))
        elif mtype == 'setParam':
            self.ISO.setParam(CID,mdata)
            log.info("Client %s setParam %s." % (str(CID), repr(mdata)))
        else:
            log.error('Unkown MSG Type ('+CID+'): ' + mtype)
    
    def sendAllDispatch(self):
        for CID in self.CIDList:
            self.sendDispatch(CID,self.ISO.getReply(CID))
    
    def sendDispatch(self, CID, dispatch):
        msg = {}
        msg["type"] = 'dispatch'
        msg["payload"] = dispatch
        self.comms.serverSendValue(CID,msg)

    def sendAllExitMsg(self):
        log.info("Sending exit message to all clients")
        msg = {}
        msg["type"] = 'exit'
        msg["payload"] = {}
        for CID in self.CIDList:
            self.comms.serverSendValue(CID,msg)
    

def getAgent(**kwargs):
    agent = ISOServerAgent()
    agent.setConfiguration(None, **kwargs)
    return agent