#!/usr/bin/env python

import logging
import scipy.io
import sys
import time

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import NonBlockingDispatchAgent
from magi.util.processAgent import initializeProcessAgent
import yaml

import numpy as np


log = logging.getLogger(__name__)


class GridDynamics(NonBlockingDispatchAgent):
    
    def __init__(self):
        NonBlockingDispatchAgent.__init__(self)
        self.configFileName = 'AGCDR_agent.mat'
        self.loadProfileConfigFileName = 'AGCDR_profiles.mat'
        self.N_iter = 100
        
    def setConfiguration(self, msg, **kwargs):
        NonBlockingDispatchAgent.setConfiguration(self, msg, **kwargs)

        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        self.loadProfileConfig = scipy.io.loadmat(self.loadProfileConfigFileName, mat_dtype=True)
        
        self.N_bus = int(self.config['N_bus']) # number of buses in the system
        self.N_ang = int(self.config['N_ang']) # number of voltage angles (excluding slack bus)
        self.N_gen = int(self.config['N_gen']) # number of (conventional) generators
        self.N_dem = int(self.config['N_dem']) # number of demand response units (specified by the user and randomly distributed in the grid)
        self.N_xi = int(self.config['N_xi']) # number of entries in the xi vector
        self.N_y = int(self.config['N_y']) #number of entries in the y vector
        
        self.Kf = 0.1;
        
        self.A3 = self.config['A3']
        self.A4 = self.config['A4']
        self.Phi = self.config['Phi']
        
        self.Gamma_P_L = self.config['Gamma_P_L']
        self.Gamma_P_G = self.config['Gamma_P_G']
        self.Gamma_P_D = self.config['Gamma_P_D']
        
        self.P_L_base = np.squeeze(self.config['P_L_base'])
        
        TotalLoadProfile = self.loadProfileConfig['TotalLoadProfile']
        
        T_start = 0 # Start time in hours (i.e. 8 => 8am)
        duration = 24 # Duration in hours
        
        # Construct P_L and P_L_hat
        index = T_start*3600/2
        scaling_signal = TotalLoadProfile[0,index:index+duration*3600/2]
        initial_magnitude = scaling_signal[0]
        scaling_signal = 1/initial_magnitude*scaling_signal
        #N_iter = len(scaling_signal)
        
        self.P_L = np.zeros((len(self.P_L_base), self.N_iter))
        self.P_L_hat = np.zeros((len(self.P_L_base), self.N_iter))
        
        for k in range(self.N_iter):
            # DETERMINE LOADS FOR THIS TIME INTERVAL
            self.P_L[:,k] = scaling_signal[k]*self.P_L_base;
            self.P_L_hat[:,k] = self.P_L_base;
            
        self.xi_current = np.zeros((self.N_xi));
        self.theta = np.zeros((self.N_ang));
        self.P_G = np.zeros((self.N_gen));
        self.P_D = np.zeros((self.N_dem));
        
        self.y = np.zeros((self.N_y, self.N_iter+1));
        self.E_D = np.zeros((self.N_dem, self.N_iter+1));
        self.rho = np.zeros((self.N_iter+1, 1));
        
        # Loading stabilized values
        self.xi_current[:] = self.config['xi'][:, -1]
        
        # Splitting components of x
        self.theta[:] = self.xi_current[0:self.N_ang]
        self.P_G[:] = self.xi_current[(self.N_ang):(self.N_ang+self.N_gen)]
        self.P_D[:] = self.xi_current[(self.N_ang+self.N_gen):(self.N_ang+self.N_gen+self.N_dem)]
        
        self.y[:, 0] = self.config['y'][:, -1]
        self.rho[0] = self.config['rho']
        self.E_D[:, 0] = self.config['E_D'][:, -1]
        
        self.collection = database.getCollection("grid_agent")
        self.collection.remove({})
        
        self.collection.insert({'k' : 0, 'y' : self.y[:, 0].tolist()})
        self.collection.insert({'k' : 0, 'rho' : self.rho[0].tolist()})
        self.collection.insert({'k' : 0, 'edr' : self.E_D[:, 0].tolist()})
          
    def receiveTheta(self, msg, k, theta):
        log.info("Received theta for k=%d", k)
        self.xi_current[0:self.N_ang] = theta
        self.theta[:] = theta
        
        time.sleep(1)
        self.compute(k)
    
    def receivePg(self, msg, k, pg):
        log.info("Received pg from %s for k=%d: %f", msg.src, k, pg)
        index = int(msg.src.split("-")[-1])
        self.xi_current[self.N_ang + index] = pg
        self.P_G[index] = pg
    
    def receivePdr(self, msg, k, pdr):
        log.info("Received pdr from %s for k=%d: %f", msg.src, k, pdr)
        index = int(msg.src.split("-")[-1])
        self.xi_current[self.N_ang + self.N_gen + index] = pdr
        self.P_D[index] = pdr
    
    def compute(self, k):
        # UPDATE GRID DYNAMICS (centralized)
        log.info("Upgrading grid dynamics")
        
        log.info("Logging x (k=%d)", k)
        log.info(self.xi_current)
        
        self.y[:, k+1] = self.Phi.dot(self.y[:, k]) + self.Gamma_P_L.dot(self.P_L[:, k]) \
                                                    + self.Gamma_P_G.dot(self.P_G[:]) \
                                                    + self.Gamma_P_D.dot(self.P_D[:])
        log.info("Logging y (k=%d)", k+1)
        log.info(self.y[:, k+1])
        self.collection.insert({'k' : k+1, 'y' : self.y[:, k+1].tolist()})

        self.rho[k+1] = self.rho[k] - self.Kf*self.A3.dot(self.y[:, k])
        log.info("Logging rho(k=%d): %f", k+1, self.rho[k+1])
        self.collection.insert({'k' : k+1, 'rho' : self.rho[k+1].tolist()})
        
        log.info("Sending rho to ISO")
        self.sendRho(k+1)
        
        self.E_D[:, k+1] = self.E_D[:, k] + self.A4.dot(self.y[:, k])
        log.info("Logging E_D (k=%d)", k+1)
        log.info(self.E_D[:, k+1])
        self.collection.insert({'k' : k+1, 'edr' : self.E_D[:, k+1].tolist()})
        
        log.info("Sending E_D to demand response agents")
        self.sendEdr(k+1)
        
    def sendEdr(self, k):
        functionName = self.sendEdr.__name__
        helpers.entrylog(log, functionName)
        
        for agentIndex in range(0, self.N_dem):
            node = "dr-"+str(agentIndex)
            edr = self.E_D[agentIndex, k]
            log.debug("Sending E_D, Node: %s, k:%d, E_D:%f", node, k, edr)
            kwargs = {'method' : 'receiveEdr', 'args' : {'k' : k, 'edr' : edr}, 'version' : 1.0}
            msg = MAGIMessage(nodes=node, docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)

        helpers.exitlog(log, functionName) 
        
    def sendRho(self, k):
        functionName = self.sendRho.__name__
        helpers.entrylog(log, functionName, locals())
        kwargs = {'method' : 'receiveRho', 'args' : {'k' : k, 'rho' : self.rho[k]}, 'version' : 1.0}
        log.debug("Sending rho: %s", kwargs['args'])
        msg = MAGIMessage(nodes="iso", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
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