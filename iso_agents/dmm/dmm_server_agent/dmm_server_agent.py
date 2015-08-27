import sys
import traceback
import threading
import random
import time
import json
import os
import io
import logging

from server_comm_service import ServerCommService
from dmm_iso import DMM_ISO
from magi.util import database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

log = logging.getLogger(__name__)

class DMMServerAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.simRunning = False
        self.configFileName = None # must be configured by MAGI

    @agentmethod()
    def initServer(self, msg):
        log.info("Initializing DMMServer...")
        
        globalConfig = None
        log.info("Attempting to read from configFile: %s" % self.configFileName)
        with open(self.configFileName, 'r') as configFile:
            globalConfig = json.load(configFile)

        self.tS = globalConfig["timeStep"]
        self.numIterations = globalConfig["numIterations"]
        self.VPP = globalConfig["vpp"]
        # self.CIDList = {}
        
        self.collection = database.getCollection(self.name)
        self.collection.remove() #reset db for each run
        
        self.comms = ServerCommService()
        self.comms.initAsServer(self.replyHandler)

        self.ISO = DMM_ISO(globalConfig["iso_params"])
        
        self.running = 0
        self.lastUpdate = 0
        self.lastUpdateList = {}
        return True
        

    @agentmethod()
    def startSimulation(self, msg):
        log.info("Starting simulation...")
        self.simRunning = True
        self.simThread = threading.Thread(target=self.runServer, name='DMMServerSimThread',target=self.serverThread))

        self.clientList = self.ISO.getClientList()
        
        for key,val in self.clientList.iteritems():
            self.lastUpdateList[key] = self.lastUpdate

        self.simThread.start()
        return True
    
    def runServer(self):
        log.info( "RunServer started...")

        try:
            log.info("CIDList len: %d" % len(self.CIDList))

            startTime=time.time()
            for t in range(1, self.numIterations + 1):
                if self.simRunning:
                    log.info("Simulation Timestep %d..." % t)
                    self.lastUpdate += 1
            
                    #Send out dispatch
                    for key,val in self.clientList.iteritems():
                        clientID = key
                        dispatch = self.ISO.getClientDispatch(clientID)

                        # TODO: Confirm that message is sent in format client is expecting
                        self.comms.serverSendValue(clientID, dispatch)
                    
                    #Utilities come in asynchronously, so scan the list until everything is refreshed
                    _sum = 0
                    while (_sum < len(self.lastUpdateList) * self.lastUpdate):
                        _sum = 0
                        for val in self.lastUpdateList.values():
                            _sum  += val

                    # TODO: (FIND OUT) How is self.ISO.df getting updated??
                    self.ISO.UpdateState(self.ISO.df)
                    state = self.ISO.getStateData()
                    state["ltime"] = time.time() - startTime
                    
                    if (self.lastUpdate) % 10 == 0:
                        self.db.collection.insert(state)

                    log.info('Completed iteration ' + str(self.lastUpdate))
                    
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
        # TODO: Confirm that this works as expected... (below)
        elif mtype == 'setUtil':
            self.ISO.setClientUtil(CID, msg)
            self.lastUpdateList[CID] = self.lastUpdate
            log.info("Client %s setUtil %s." % (str(CID), repr(mdata)))
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