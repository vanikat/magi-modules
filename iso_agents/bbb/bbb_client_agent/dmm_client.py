from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.util.distributions import *

import logging
import random
import sys
import socket
import json
import numpy as np
from DMM_COMM import DMM_COMM

"""
unit testing code:
sudo apt-get install python-numpy python-scipy python-h5py
cd /proj/cmregx/exp/smalldmmcmrex/expdata/iso_client
sudo sysctl -w net.core.somaxconn=1024

batch clients:
from iso_client_test import iso_client_test
ict=iso_client_test('/proj/cmregx/exp/smalldmmcmrex/expdata/client_case30.json','10.1.1.2')
ict.loadClients('clist30.txt')
ict.startClients()


single client:
from iso_client import iso_client
iclt=iso_client()
iclt.clientID='G-1'
iclt.scenarioFile='/proj/cmregx/exp/smalldmmcmrex/expdata/client_case4.json'
iclt.isoServer='10.1.1.2'
iclt.connectISO('')

"""


class iso_client(DispatchAgent):
    def __init__(self):
        DispatchAgent.__init__(self)
        return

    
    @agentmethod()
    def connectISO(self, msg):
        nstr=self.clientID
        splitstr=nstr.split('-')
        self.clientType=splitstr[0]
        self.clientIdx=int(splitstr[1])
        f=open(self.scenarioFile,'r')
        jsonVals=json.loads(f.read())
        
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
        
        self.dmc=DMM_COMM()
        self.dmc.initAsClient(self.isoServer,self.clientID,self.clientReplyHandler)
        return 
    
    def clientReplyHandler(self,clientID,powerLevel):
        tPMax=self.PMax
        tPMin=self.PMin
        """
        if self.clientType=='G':
            PgMaxk=0
            PgMaxf=0
            PgMaxf=self.PMax*(1+(self.delta/100.0))
            PgMaxk=PgMaxk-np.minimum((PgMaxk-powerLevel)*self.gamma,PgMaxk-PgMaxf)
            tPMax=PgMaxk
        """
        
        util = self.b+self.c*powerLevel
        
        util += self.M/((powerLevel-tPMax)**2)-self.M/((powerLevel-tPMin)**2)
        #print clientID + ' b: ' + str(self.b) + ' c: ' + str(self.c) + ' PL: ' + str(powerLevel) + ' u: ' + str(util)
        
        
        return util

    @agentmethod()
    def cleanup(self,msg):
        self.dmc.close()
        return

def getAgent():
    agent = iso_client()
    return agent

if __name__ == "__main__":
    agent = iso_client()
    initializeProcessAgent(agent, sys.argv)
    agent.run()