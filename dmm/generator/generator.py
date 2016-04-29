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
        
        self.N_gen = np.squeeze(self.config['N_gen'])
        
        self.c_G = self.config['c_G'][self.index, self.index]
        self.b_G = self.config['b_G'][self.index]
        
        self.Kmu3 = 0.01;
        self.Kmu4 = 0.01;
        
        self.P_G = np.zeros(self.N_iter+1);
        self.P_Gmax = np.squeeze(self.config['P_Gmax'][self.index])
        self.P_Gmin = np.squeeze(self.config['P_Gmin'][self.index])
        self.grad_f = np.zeros(self.N_iter+1);
        
        self.mu3 = np.zeros(self.N_iter+1);
        self.mu4 = np.zeros(self.N_iter+1);
        
        # Loading stabilized values
        self.mu3[0] = self.config['mu3'][self.index]
        self.mu4[0] = self.config['mu4'][self.index]
        
        #Attack
        self.deception = 0
        self.gradFDeception = 0
        
    def receivePg(self, msg, k, pg):
        log.info("Received P_G: %f(k=%d)", pg, k)
        
        if self.active:
            self.P_G[k] = pg + self.deception
        else:
            log.info("Agent is inactive")
            self.P_G[k] = self.P_G[k-1]
            
        if self.P_G[k] < self.P_Gmin:
            self.P_G[k] = self.P_Gmin
        elif self.P_G[k] > self.P_Gmax:
            self.P_G[k] = self.P_Gmax
            
        self.sendPg(k)
        
        self.computeGradF(k)
        self.sendGradF(k)
        
        self.computeMu(k)
    
    def sendPg(self, k):
        functionName = self.sendPg.__name__
        helpers.entrylog(log, functionName)
        pg = self.P_G[k]
        log.info("Sending P_G: %f (k=%d)", pg, k)
        kwargs = {'method' : 'receivePg', 'args' : {'k' : k, 'pg' : pg}, 'version' : 1.0}
        msg = MAGIMessage(nodes="grid", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        if self.active:
            msg = MAGIMessage(nodes="iso", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)
        else:
            log.info("Agent is inactive. No P_G reply sent to ISO.")
        helpers.exitlog(log, functionName)
    
    def computeGradF(self, k):
        functionName = self.computeGradF.__name__
        helpers.entrylog(log, functionName)
        self.grad_f[k] = self.c_G*(self.P_G[k]) - self.mu3[k] + self.mu4[k] + self.b_G
        helpers.exitlog(log, functionName)
        
    def sendGradF(self, k):
        functionName = self.sendGradF.__name__
        helpers.entrylog(log, functionName, locals())
        if self.active:
            grad_f = self.grad_f[k] + self.gradFDeception
            log.info("Sending grad_f: %f (k=%d)", grad_f, k)
            kwargs = {'method' : 'receiveGradF', 'args' : {'k' : k, 'grad_f' : grad_f}, 'version' : 1.0}
            #log.info("Sending reply: %s", kwargs['args'])
            msg = MAGIMessage(nodes="iso", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)
        else:
            log.info("Agent is inactive")
        helpers.exitlog(log, functionName)
        
    def computeMu(self, k):
        functionName = self.computeMu.__name__
        helpers.entrylog(log, functionName)
        self.mu3[k+1] = max(0, self.mu3[k] + self.Kmu3*(self.P_Gmin-self.P_G[k]))
        self.mu4[k+1] = max(0, self.mu4[k] + self.Kmu4*(self.P_G[k]-self.P_Gmax))
        log.info("Computed Mu. k=%d, mu3:%f, mu4:%f", k+1, self.mu3[k+1], self.mu4[k+1])
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
    
    def startDeception(self, msg, deception, nodes):
        log.info("Attacked nodes: %s", nodes)
        if self.hostname in nodes:
            log.info("Activated deception %d", deception)
            self.deception = deception
        
    def stopDeception(self, msg, nodes):
        self.deception = 0

    def startGradFDeception(self, msg, deception, nodes):
        log.info("Attacked nodes: %s", nodes)
        if self.hostname in nodes:
            self.gradFDeception = deception
            log.info("Activated grad_f deception %d", deception)
    
    def stopGradFDeception(self, msg, nodes):
        self.gradFDeception = 0        
            
            
def getAgent(**kwargs):
    agent = Generator()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = Generator()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()