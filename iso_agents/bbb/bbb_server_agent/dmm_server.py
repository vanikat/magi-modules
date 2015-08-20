from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.util.distributions import *

import logging
import random
import sys
import socket
import json
import time
import csv
import code
from DMM_COMM import DMM_COMM
from DMM_ISO import DMM_ISO
from threading import Thread

"""
Unit Testing:
cd /proj/cmregx/exp/smalldmmcmrex/expdata/iso_server
sudo apt-get install python-numpy python-scipy python-h5py
sudo sysctl -w net.core.somaxconn=1024
python

from iso_server import iso_server
iso=iso_server()
iso.dmmCaseFile='/proj/cmregx/exp/smalldmmcmrex/expdata'
iso.caseNum=30
iso.maxIter=10000
iso.startISOServer('')
#Wait some time, start clients, etc
iso.stopISOServer('')

"""

class iso_server(DispatchAgent):
    def __init__(self):
        DispatchAgent.__init__(self)
        self.maxIter=10000
        return
        

    def serverReplyHandler(self,clientID,utility):
        self.DISO.setClientUtil(clientID,utility)
        self.lastUpdateList[clientID]=self.lastUpdate
    
    def serverThread(self):
        startTime=time.time()
        fstr=self.dmmCaseFile+'/statelog'+str(self.caseNum)+'.csv'
        f=open(fstr,'wt')
        writer=csv.writer(f)
        while self.running and self.lastUpdate < self.maxIter:
            self.lastUpdate+=1
            #Send out dispatch
            for key,val in self.clientList.iteritems():
                clientID=key
                dispatch=self.DISO.getClientDispatch(clientID)
                self.dmc.serverSendValue(clientID,dispatch)
            #Utilities come in asynchronously, so scan the list until everything is refreshed
            sum=0
            while (sum < len(self.lastUpdateList)*self.lastUpdate):
                sum=0
                for key,val in self.lastUpdateList.iteritems():
                    sum += val
            self.DISO.UpdateState(self.DISO.df)
            dTime=time.time()-startTime
            state=self.DISO.getStateData()
            ltime=[dTime]
            if (self.lastUpdate)%10==0:
                writer.writerow(ltime+state)
            print 'Completed iteration ' + str(self.lastUpdate)
            #if self.lastUpdate >= 2:
            #   code.interact(local=locals())
        
        f.close()
    
    @agentmethod()
    def startISOServer(self, msg):
        self.DISO=DMM_ISO(self.dmmCaseFile,self.caseNum,1,0.1,0.1,2,0.001)
        self.clientList=self.DISO.getClientList()
        self.dmc=DMM_COMM()
        self.dmc.initAsServer(self.serverReplyHandler)
        self.running=1
        self.lastUpdate=0
        self.lastUpdateList={}
        for key,val in self.clientList.iteritems():
            self.lastUpdateList[key]=self.lastUpdate
        nthread=Thread(name='isoServerThread',target=self.serverThread)
        #Block until all clients connected
        while len(self.dmc.slock) < len(self.clientList):
            pass
        nthread.start()
    
    @agentmethod()
    def stopISOServer(self,msg):
        self.dmc.close()
        self.running=0
        return
    

def getAgent():
    agent = iso_client()
    return agent

if __name__ == "__main__":
    agent = iso_server()
    initializeProcessAgent(agent, sys.argv)
    agent.run()