#!/usr/bin/env python

import logging
import scipy.io
import sys

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers
from magi.util.agent import DispatchAgent
from magi.util.processAgent import initializeProcessAgent
import yaml

import numpy as np


log = logging.getLogger(__name__)

class DemandResponse(DispatchAgent):
    
    def __init__(self):
        DispatchAgent.__init__(self)
        self.isoDock = "iso_dock"
        self.gridDynamicsDock = "grid_dock"
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        self.active = True
        
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        
        log.info("Hostname: %s", self.hostname)
        from magi.testbed import testbed
        self.hostname = testbed.nodename
        log.info("Hostname: %s", self.hostname)
        
        self.index = int(self.hostname.split("-")[-1])
        
        self.Ndr = np.squeeze(self.config['Ndr'])
        
        self.cdr = self.config['cdr'][self.index, self.index]
        self.bdr = self.config['bdr'][self.index]
        
        self.Kmu3 = 0.08;
        self.Kmu4 = 0.08;
        
        self.Pdr = np.zeros(self.N_iter+1);
        self.Edr = np.zeros(self.N_iter+1);
        self.grad_f = np.zeros(self.N_iter+1);
        
        self.mu3 = np.zeros(self.N_iter+1);
        self.mu4 = np.zeros(self.N_iter+1);
        
        # Loading stabilized values
        self.Edr[0] = self.config['Edr'][self.index]
        self.mu3[0] = self.config['mu3'][self.index]
        self.mu4[0] = self.config['mu4'][self.index]
        
    def receivePdr(self, msg, k, pdr):
        log.info("Received Pdr: %f(k=%d)", pdr, k)
        
        if self.active:
            self.Pdr[k] = pdr
        else:
            log.info("Agent is inactive")
            self.Pdr[k] = self.Pdr[k-1]
            
        self.sendPdr(k)
        
        self.computeGradF(k)
        self.sendGradF(k)
        
        self.computeMu(k)
        
    def receiveEdr(self, msg, k, edr):
        log.info("Received Edr: %f(k=%d)", edr, k)
        self.Edr[k] = edr
        
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu3[k+1] = max(0, self.mu3[k] + self.Kmu3*(-self.Edr[k]-self.Pdr[k]))
        self.mu4[k+1] = max(0, self.mu4[k] + self.Kmu4*(self.Pdr[k]+ self.Edr[k]))
        log.info("Computed Mu. k=%d, mu3:%f, mu4:%f", k+1, self.mu3[k+1], self.mu4[k+1])
        helpers.exitlog(log, functionName)
        
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = -self.cdr*(self.Pdr[k]) - self.mu3[k] + self.mu4[k] - self.bdr
        helpers.exitlog(log, functionName)
    
    def sendGradF(self, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName)
        if self.active:
            grad_f = self.grad_f[k]
            log.info("Sending grad_f: %f (k=%d)", grad_f, k)
            kwargs = {'method' : 'receiveGradF', 'args' : {'k' : k, 'grad_f' : grad_f}, 'version' : 1.0}
            msg = MAGIMessage(nodes="iso", docks=self.isoDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)
        else:
            log.info("Agent is inactive")
        helpers.exitlog(log, functionName)
    
    def sendPdr(self, k):
        functionName = self.sendPdr.__name__
        helpers.entrylog(log, functionName)
        pdr = self.Pdr[k]
        log.info("Sending Pdr: %f (k=%d)", pdr, k)
        kwargs = {'method' : 'receivePdr', 'args' : {'k' : k, 'pdr' : pdr}, 'version' : 1.0}
        msg = MAGIMessage(nodes="grid", docks=self.gridDynamicsDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    def deactivate(self, msg, nodes):
        log.info("Nodes to deactivate: %s", nodes)
        if self.hostname in nodes:
            log.info("Deactivating")
            self.active = False
            
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