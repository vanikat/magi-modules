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

class Generator(DispatchAgent):
    
    def __init__(self):
        DispatchAgent.__init__(self)
        self.isoDock = "iso_dock"
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        
        log.info("Loading Config File: %s", self.configFileName)
        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        
        log.info("Hostname: %s", self.hostname)
        from magi.testbed import testbed
        self.hostname = testbed.nodename
        log.info("Hostname: %s", self.hostname)
        
        self.index = int(self.hostname.split("-")[-1])
        
        self.Ngc = np.squeeze(self.config['Ngc'])
        
        self.cgc = self.config['cgc'][self.index, self.index]
        self.bgc = self.config['bgc'][self.index]
        
        self.Kmu1 = 0.02;
        self.Kmu2 = 0.02;
        
        self.Pg = np.zeros(self.N_iter+1);
        self.Pgcmax = np.squeeze(self.config['Pgcmax'][self.index])
        self.Pgcmin = np.squeeze(self.config['Pgcmin'][self.index])
        self.grad_f = np.zeros(self.N_iter+1);
        self.mu1 = np.zeros(self.N_iter+1);
        self.mu2 = np.zeros(self.N_iter+1);
        
        self.computeGradF(0)
    
    def sendGradF(self, msg, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName, locals())
        kwargs = {'method' : 'receiveGradF', 'args' : {'k' : k, 'grad_f' : self.grad_f[k]}, 'version' : 1.0}
        log.info("Sending reply: %s", kwargs['args'])
        msg = MAGIMessage(nodes=msg.src, docks=self.isoDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    def receivePg(self, msg, k, pg):
        log.info("Received Pg: %f(k=%d)", pg, k)
        self.Pg[k] = pg
        
        self.computeMu(k)
        self.computeGradF(k)
        
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu1[k] = max(0, self.mu1[k-1] + self.Kmu1*(self.Pgcmin-self.Pg[k-1]))
        self.mu2[k] = max(0, self.mu2[k-1] + self.Kmu2*(self.Pg[k-1]-self.Pgcmax))
        log.info("Computed Mu. k=%d, mu1:%f, mu2:%f", k, self.mu1[k], self.mu2[k])
        helpers.exitlog(log, functionName)
        
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = self.cgc*(self.Pg[k]) - self.mu1[k] + self.mu2[k] + self.bgc
        helpers.exitlog(log, functionName)

def getAgent(**kwargs):
    agent = Generator()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = Generator()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()