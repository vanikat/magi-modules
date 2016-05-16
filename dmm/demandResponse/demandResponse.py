#!/usr/bin/env python

import logging
import scipy.io
import sys

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers
from magi.util.agent import NonBlockingDispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
import yaml

from commClient import ClientCommService
import numpy as np


log = logging.getLogger(__name__)

class DemandResponse(NonBlockingDispatchAgent):
    
    def __init__(self):
        NonBlockingDispatchAgent.__init__(self)
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        self.active = True
    
    def setConfiguration(self, msg, **kwargs):
        NonBlockingDispatchAgent.setConfiguration(self, msg, **kwargs)
        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        
        log.info("Hostname: %s", self.hostname)
        from magi.testbed import testbed
        self.hostname = testbed.nodename
        log.info("Hostname: %s", self.hostname)
        
        self.index = int(self.hostname.split("-")[-1])
        
        self.N_dem = np.squeeze(self.config['N_dem'])
        self.K_E = 0 # energy payback (turned off for now)
        
        self.c_D = self.config['c_D'][self.index, self.index]
        self.b_D = self.config['b_D'][self.index]
        
        self.Kmu5 = 0.05;
        self.Kmu6 = 0.05;
        
        self.P_D = np.zeros(self.N_iter+1);
        self.P_Dmax = np.squeeze(self.config['P_Dmax'][self.index])
        self.P_Dmin = np.squeeze(self.config['P_Dmin'][self.index])
        self.E_D = np.zeros(self.N_iter+1);
        self.grad_f = np.zeros(self.N_iter+1);
        
        self.mu5 = np.zeros(self.N_iter+1);
        self.mu6 = np.zeros(self.N_iter+1);
        
        # Loading stabilized values
        self.E_D[0] = self.config['E_D'][self.index]
        self.mu5[0] = self.config['mu5'][self.index]
        self.mu6[0] = self.config['mu6'][self.index]
        
        #Out of Market
        self.lastPdrRcvdTs = -1
        self.currentGridTs = -1
        
        self.commClient = None
    
    @agentmethod()
    def initCommClient(self, msg):
        self.commClient = ClientCommService(self.hostname)
        self.commClient.initCommClient("iso", self.isoPdrRequestHandler)
    
    @agentmethod()
    def stop(self, msg):
        NonBlockingDispatchAgent.stop(self, msg)
        if self.commClient:
            self.commClient.stop()
        
    def isoPdrRequestHandler(self, msgData):
        log.debug("isoPdrRequestHandler: %s", msgData)
        
        dst = msgData['dst']
        if dst != self.hostname:
            log.error("Message sent to incorrect destination.")
            return
        
        k = msgData['k']
        pdr = msgData['pdr']
        
        if k < self.currentGridTs:
            log.error("Stale message. Dropping. Current TS: %d, Msg TS: %d", 
                      self.currentGridTs, k)
            return
        
        if self.active:
            log.info("Received P_D: %f(k=%d)", pdr, k)
            self.P_D[k] = pdr
            
            if self.P_D[k] < self.P_Dmin:
                self.P_D[k] = self.P_Dmin
            elif self.P_D[k] > self.P_Dmax:
                self.P_D[k] = self.P_Dmax
            
            self.lastPdrRcvdTs = k
            
            self.computeGradF(k)
            self.sendGradF(k)
            
        else:
            log.info("Agent is inactive")
        
        self.computeMu(k)
        
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = -self.c_D*(self.P_D[k]) - self.mu5[k] + self.mu6[k] - self.b_D
        helpers.exitlog(log, functionName)
    
    def sendGradF(self, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName)
        pdr = self.P_D[k]
        grad_f = self.grad_f[k]
        log.info("Sending grad_f: %f, P_D: %f (k=%d)", grad_f, pdr, k)
        self.commClient.sendData({'k' : k, 'pdr': pdr, 'grad_f' : grad_f})
        helpers.exitlog(log, functionName)
    
    @agentmethod()
    def sendPdr(self, msg, k):
        functionName = self.sendPdr.__name__
        helpers.entrylog(log, functionName)
        self.currentGridTs = k
        if k > self.lastPdrRcvdTs:
            self.P_D[k] = self.P_D[self.lastPdrRcvdTs]
        pdr = self.P_D[k]
        log.info("Sending P_D: %f (k=%d)", pdr, k)
        kwargs = {'method' : 'receivePdr', 'args' : {'k' : k, 'pdr' : pdr}, 'version' : 1.0}
        msg = MAGIMessage(nodes="grid", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    @agentmethod()
    def receiveEdr(self, msg, k, edr):
        log.info("Received E_D: %f(k=%d)", edr, k)
        self.E_D[k] = edr
    
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu5[k+1] = max(0, self.mu5[k] + self.Kmu5*(-self.P_D[k] - self.K_E*self.E_D[k] + self.P_Dmin))
        self.mu6[k+1] = max(0, self.mu6[k] + self.Kmu6*(self.P_D[k] + self.K_E*self.E_D[k] - self.P_Dmax))
        log.info("Computed Mu. k=%d, mu5:%f, mu6:%f", k+1, self.mu5[k+1], self.mu6[k+1])
        helpers.exitlog(log, functionName)
    
    @agentmethod()
    def deactivate(self, msg, nodes):
        log.info("Nodes to deactivate: %s", nodes)
        if self.hostname in nodes:
            log.info("Deactivating")
            self.active = False
    
    @agentmethod()
    def activate(self, msg, nodes):
        log.info("Nodes to activate: %s", nodes)
        if self.hostname in nodes:
            log.info("Activating")
            self.active = True
    

def getAgent(**kwargs):
    agent = DemandResponse()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = DemandResponse()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()