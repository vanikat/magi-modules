import sys
import traceback
from os.path import basename

import threading
import random
import time

from server_comm_service import ServerCommService
from bbb_iso import BBB_ISO
from magi.util import database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

import logging
log = logging.getLogger(__name__)

import os

class ISOServerAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.simRunning = False
        # self.data_filename = DATA_DIR + 'BBBLog.csv'

    @agentmethod()
    def initServer(self, msg):
        log.info("Initializing ISOServer...")
        self.collection = database.getCollection(self.name)
        self.comms = ServerCommService()
        self.comms.initAsServer(self.replyHandler)
        self.BBB = BBB_ISO()
        self.CIDList = {}
        return True

    @agentmethod()
    def startSimulation(self, msg):
        log.info("Starting simulation...")
        self.simRunning = True
        self.simThread = threading.Thread(target=self.runServer)
        self.simThread.start()
        return True
    
    def runServer(self, Ts=0.2):
        log.info( "RunServer started...")

        try:
            log.info("CIDList: %s" % repr(self.CIDList))
            log.info("BBB.unitList: %s" % repr(self.BBB.unitList))
            time.sleep(Ts) # let all clients connect and get ready
            self.BBB.Ts = Ts

            for i in range(1, 100):
                if self.simRunning:
                    log.info("Simulation Timestep %d..." % i)
                    time.sleep(self.BBB.Ts)
                    pDispatch = random.randint(100,120)
                    log.info("AgileBalancing %d units of power..." % pDispatch)
                    self.BBB.agileBalancing(i,pDispatch)
                    
                    log.info("Sending dispatch to all units...")
                    self.sendAllDispatch()
                    
                    log.info("Logging current state...")
                    stats = self.BBB.generateStats(i, pDispatch)
                    self.collection.insert(stats)
                else:
                    log.info( "Simulation has been told to exit, timestep = %d" % i)
                    break
        except Exception, e:
            log.info("Thread %s threw an exception during main loop" % threading.currentThread().name)
            exc_type, exc_value, exc_tb = sys.exc_info()
            log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))

        log.info("RunServer ending...")

    @agentmethod()
    def stopSimulation(self, msg):
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
            self.BBB.registerClient(CID, mdata)
            self.CIDList[CID] = True
            log.info("Client %s registered." % str(CID))
        elif mtype == 'deregister':
            self.BBB.deregisterClient(CID)
            del self.CIDList[CID]
            log.info("Client %s de-registered." % str(CID))
        elif mtype == 'setParam':
            self.BBB.setParam(CID,mdata)
            log.info("Client %s setParam %s." % (str(CID), repr(mdata)))
        else:
            log.error('Unkown MSG Type ('+CID+'): ' + mtype)
    
    def sendAllDispatch(self):
        log.info("CID List: %s" % repr(self.CIDList))
        log.info("BBB.unitList: %s" % repr(self.BBB.unitList))
        for CID in self.CIDList:
            self.sendDispatch(CID,self.BBB.getReply(CID))
    
    def sendDispatch(self, CID, dispatch):
        msg = {}
        msg["type"] = 'dispatch'
        msg["payload"] = dispatch
        self.comms.serverSendValue(CID,msg)
    

def getAgent(**kwargs):
    agent = ISOServerAgent()
    agent.setConfiguration(None, **kwargs)
    return agent