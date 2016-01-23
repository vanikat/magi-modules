#!/usr/bin/env python

import logging
import scipy.io
import sys

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import DispatchAgent
from magi.util.processAgent import initializeProcessAgent
import yaml

import numpy as np


log = logging.getLogger(__name__)


class GridDynamics(DispatchAgent):
    
    def __init__(self):
        DispatchAgent.__init__(self)
        
        self.isoGroup = "iso_group"
        self.isoDock = "iso_dock"
        self.loadGenDock = "loadGen_dock"
        
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        
        self.Ndc = int(self.config['Ndc'])
        self.Nde = int(self.config['Nde'])
        self.Ngc = int(self.config['Ngc'])
        self.Ndr = int(self.config['Ndr'])
        
        self.K_E = self.config['K_E']
        self.Kf = 0.2;
        
        Agrid = self.config['Agrid']
        self.A3 = self.config['A3']
        self.A4 = self.config['A4']
        self.Phi = self.config['Phi']
        self.Gamma_x = self.config['Gamma_x']
        self.Gamma_d = self.config['Gamma_d']
        
        self.Pdc = self.config['Pdc']

        if self.config.has_key('Pe'):
            self.Pe = self.config['Pe']
        else:
            self.Pdc = addColumn(self.Pdc, self.N_iter-1)
            for k in range(self.N_iter):
                # DETERMINE LOADS FOR THIS TIME INTERVAL
                self.Pdc[:, k] = self.Pdc[:, 0]
            self.Pe = self.Pdc
    
        # Calculate Delta (i.e. the difference between actual and predicted)
        self.Delta = self.Pdc - self.Pe;
        
        self.d = np.concatenate((self.Pdc, self.Delta))
        
        self.x = np.zeros((self.Nde+self.Ndr+self.Ngc, self.N_iter+1));
        
        self.y = np.zeros((len(Agrid), self.N_iter+1));
        self.Edr = np.zeros((self.Ndr, self.N_iter+1));
        self.rho = np.zeros((self.N_iter+1, 1));
        
        self.collection = database.getCollection("grid_agent")
        self.collection.remove({})
          
    def receiveX(self, msg, k, x):
        log.info("Received x for k=%d", k)
        self.x[:, k] = x
        
        self.compute(k)
        
    def compute(self, k):
        # UPDATE GRID DYNAMICS (centralized)
        log.info("Upgrading grid dynamics")
        
        self.y[:, k+1] = self.Phi.dot(self.y[:, k]) + self.Gamma_d.dot(self.d[:, k]) + self.Gamma_x.dot(self.x[:, k])
        log.info("Logging y (k=%d)", k+1)
        log.info(self.y[:, k+1])
        self.collection.insert({'k' : k+1, 'y' : self.y[:, k+1].tolist()})

        self.rho[k+1] = self.rho[k] - self.Kf*self.A3.dot(self.y[:, k])
        log.info("Logging rho(k=%d): %f", k+1, self.rho[k+1])
        self.collection.insert({'k' : k+1, 'rho' : self.rho[k+1].tolist()})
        
        log.info("Sending rho to ISO")
        self.sendRho(k+1)
        
        self.Edr[:, k+1] = self.Edr[:, k] + self.K_E.dot(self.A4).dot(self.y[:, k])
        log.info("Logging Edr (k=%d)", k+1)
        log.info(self.Edr[:, k+1])
        self.collection.insert({'k' : k+1, 'edr' : self.Edr[:, k+1].tolist()})
        
        log.info("Sending Edr to demand response agents")
        self.sendEdr(k+1)
        
    def sendEdr(self, k):
        functionName = self.sendEdr.__name__
        helpers.entrylog(log, functionName)
        
        for agentIndex in range(0, self.Ndr):
            node = "dr-"+str(agentIndex)
            edr = self.Edr[agentIndex, k]
            log.debug("Sending Edr, Node: %s, k:%d, Edr:%f", node, k, edr)
            kwargs = {'method' : 'receiveEdr', 'args' : {'k' : k, 'edr' : edr}, 'version' : 1.0}
            msg = MAGIMessage(nodes=node, docks=self.loadGenDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)

        helpers.exitlog(log, functionName) 
        
    def sendRho(self, k):
        functionName = self.sendRho.__name__
        helpers.entrylog(log, functionName, locals())
        kwargs = {'method' : 'receiveRho', 'args' : {'k' : k, 'rho' : self.rho[k]}, 'version' : 1.0}
        log.debug("Sending rho: %s", kwargs['args'])
        msg = MAGIMessage(groups=self.isoGroup, docks=self.isoDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName) 

def addColumn(arr, numOfColumns=1):
    arr = np.append(arr, np.zeros((len(arr), numOfColumns)), axis=1)
    return arr

def getAgent(**kwargs):
    agent = GridDynamics()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = GridDynamics()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()