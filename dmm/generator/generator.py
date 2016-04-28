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
        self.gridDynamicsDock = "grid_dock"
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        self.active = True
        
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
        
        # Loading stabilized values
        self.mu1[0] = self.config['mu1'][self.index]
        self.mu2[0] = self.config['mu2'][self.index]
        
    def receivePg(self, msg, k, pg):
        log.info("Received Pg: %f(k=%d)", pg, k)
        
        if self.active:
            self.Pg[k] = pg
        else:
            log.info("Agent is inactive")
            self.Pg[k] = self.Pg[k-1]
            
        if self.Pg[k] < self.Pgcmin:
            self.Pg[k] = self.Pgcmin
        elif self.Pg[k] > self.Pgcmax:
            self.Pg[k] = self.Pgcmax
            
        self.sendPg(k)
        
        self.computeGradF(k)
        self.sendGradF(k)
        
        self.computeMu(k)
        
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu1[k+1] = max(0, self.mu1[k] + self.Kmu1*(self.Pgcmin-self.Pg[k]))
        self.mu2[k+1] = max(0, self.mu2[k] + self.Kmu2*(self.Pg[k]-self.Pgcmax))
        log.info("Computed Mu. k=%d, mu1:%f, mu2:%f", k+1, self.mu1[k+1], self.mu2[k+1])
        helpers.exitlog(log, functionName)
        
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = self.cgc*(self.Pg[k]) - self.mu1[k] + self.mu2[k] + self.bgc
        helpers.exitlog(log, functionName)
        
    def sendGradF(self, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName, locals())
        if self.active:
            grad_f = self.grad_f[k]
            log.info("Sending grad_f: %f (k=%d)", grad_f, k)
            kwargs = {'method' : 'receiveGradF', 'args' : {'k' : k, 'grad_f' : grad_f}, 'version' : 1.0}
            log.info("Sending reply: %s", kwargs['args'])
            msg = MAGIMessage(nodes="iso", docks=self.isoDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)
        else:
            log.info("Agent is inactive")
        helpers.exitlog(log, functionName)
        
    def sendPg(self, k):
        functionName = self.sendPg.__name__
        helpers.entrylog(log, functionName)
        pg = self.Pg[k]
        log.info("Sending Pg: %f (k=%d)", pg, k)
        kwargs = {'method' : 'receivePg', 'args' : {'k' : k, 'pg' : pg}, 'version' : 1.0}
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
    agent = Generator()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = Generator()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()