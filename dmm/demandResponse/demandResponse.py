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
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        
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
        
        self.computeGradF(0)
        
    def sendGradF(self, msg, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName)
        kwargs = {'method' : 'receiveGradF', 'args' : {'k' : k, 'grad_f' : self.grad_f[k]}, 'version' : 1.0}
        log.info("Sending reply: %s", kwargs['args'])
        msg = MAGIMessage(nodes=msg.src, docks=self.isoDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    def receivePdr(self, msg, k, pdr):
        log.info("Received Pdr: %f(k=%d)", pdr, k)
        self.Pdr[k] = pdr
        
    def receiveEdr(self, msg, k, edr):
        log.info("Received Edr: %f(k=%d)", edr, k)
        self.Edr[k] = edr
        
        self.computeMu(k)
        self.computeGradF(k)
        
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu3[k] = max(0, self.mu3[k-1] + self.Kmu3*(-self.Edr[k-1]-self.Pdr[k-1]))
        self.mu4[k] = max(0, self.mu4[k-1] + self.Kmu4*(self.Pdr[k-1]+ self.Edr[k-1]))
        log.info("Computed Mu. k=%d, mu3:%f, mu4:%f", k, self.mu3[k], self.mu4[k])
        helpers.exitlog(log, functionName)
        
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = -self.cdr*(self.Pdr[k]) - self.mu3[k] + self.mu4[k] - self.bdr
        helpers.exitlog(log, functionName)
        

def getAgent(**kwargs):
    agent = DemandResponse()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = DemandResponse()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()