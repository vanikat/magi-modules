#!/usr/bin/env python

import logging
import scipy.io
import sys
import threading
import time

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import DispatchAgent
from magi.util.processAgent import initializeProcessAgent
import yaml

import numpy as np


log = logging.getLogger(__name__)


class ISO(DispatchAgent):
    
    def __init__(self):
        DispatchAgent.__init__(self)
        
        self.loadGenGroup = ["dr_group", "gen_group"]
        self.loadGenDock = "loadGen_dock"
        
        self.gridDynamicsGroup = "grid_group"
        self.gridDynamicsDock = "grid_dock"
        
        self.configFileName = 'AGCDR_agent.mat'
        self.N_iter = 100
        
        self.thread = None
        self.active = True
        
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        
        log.info("Loading Config File: %s", self.configFileName)
        self.config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        
        self.Ndc = int(self.config['Ndc'])
        self.Nde = int(self.config['Nde'])
        self.Ngc = int(self.config['Ngc'])
        self.Ndr = int(self.config['Ndr'])
        self.Nt = int(self.config['Nt'])
        self.Nx = int(self.config['Nx'])
        
        self.Pdc = self.config['Pdc']

        if self.config.has_key('Pe'):
            self.Pe = self.config['Pe']
        else:
            self.Pdc = addColumn(self.Pdc, self.N_iter-1)
            for k in range(self.N_iter):
                # DETERMINE LOADS FOR THIS TIME INTERVAL
                self.Pdc[:, k] = self.Pdc[:, 0]
            self.Pe = self.Pdc
        
        self.B_lineR = self.config['B_lineR']
        self.N = self.config['N']
        self.Hbarinv = self.config['Hbarinv']
        
        self.A1 = self.config['A1']
        self.A2 = self.config['A2']
        
        self.Pmax = np.squeeze(self.config['Pmax'])
        self.Bias = np.squeeze(self.config['Bias'])
        
        # gains
        self.alpha = 0.9
        self.Kmu5 = 0.01*np.eye(self.Nt);
        self.Kmu6 = 0.01*np.eye(self.Nt);
        
        self.grad_f = np.zeros((self.Nx, self.N_iter));
        self.grad_L = np.zeros((self.Nx, self.N_iter));
        self.lambda_hat = np.zeros((self.Ndc, self.N_iter));
        
        self.grad_f_current = np.zeros((self.Nx))
        
        self.x = np.zeros((self.Nde+self.Ndr+self.Ngc, self.N_iter+1));
        self.theta = np.zeros((self.Nde, self.N_iter+1));
        self.Pdr = np.zeros((self.Ndr, self.N_iter+1));
        self.Pg = np.zeros((self.Ngc, self.N_iter+1));
        
        self.mu5 = np.zeros((self.Nt, self.N_iter+1));
        self.mu6 = np.zeros((self.Nt, self.N_iter+1));
        
        self.rho = np.zeros((self.N_iter+1, 1));
        
        self.collection = database.getCollection("iso_agent")
        self.collection.remove({})
    
    def runAgent(self, msg):
        functionName = self.runAgent.__name__
        helpers.entrylog(log, functionName, level=logging.INFO)
        self.thread = threading.Thread(target=self.runSimulation)
        self.thread.start()
        helpers.exitlog(log, functionName, level=logging.INFO)
        
    def runSimulation(self):
        functionName = self.runSimulation.__name__
        helpers.entrylog(log, functionName, level=logging.INFO)
        
        lastItrTS = 0
        for k in range(self.N_iter):
            
            if not self.active:
                break
            
            if time.time() < lastItrTS + 2:
                time.sleep(lastItrTS + 2 - time.time())
                
            lastItrTS = time.time()
            
            # voltage angles (computed by ISO)
            log.info("Computing voltage angles")
            self.grad_f_current[0:self.Nde] = self.B_lineR.conj().transpose().dot(self.mu6[:, k] - self.mu5[:, k])
            
            # demand response (computed by agents)
            # generators (computed by agents)
            log.info("Requesting gradient of f")
            self.requestGradF(k)
            #self.requestRho(k)
            
            #TODO: Wait to receive grad_fs
            time.sleep(1) 
            
            self.grad_f[:, k] = self.grad_f_current[:]
            log.info("Logging grad_f (k=%d)", k)
            log.info(self.grad_f[:, k])
            
            # compute lambda_hat (at ISO)
            log.info("Computing lamda_hat")
            self.lambda_hat[:, k] = self.A1.dot(self.N.conj().transpose().dot(self.x[:, k]) 
                                                     + self.Bias*self.rho[k] + self.Pdc[:, k] - self.A2.dot(self.grad_f[:, k]))
            
            # compute gradient of Lagrangian (at ISO)
            log.info("Computing gradient of Lagrangian")
            self.grad_L[:, k] = self.grad_f[:, k] + self.N.dot(self.lambda_hat[:, k])
            
            # update x vector (at ISO, then sent to agents)
            log.info("Updating x")
            self.x[:, k+1] = self.x[:, k] - self.alpha*self.Hbarinv.dot(self.grad_L[:, k])
            
            log.info("Logging x (k=%d)", k+1)
            log.info(self.x[:, k+1])
            
            log.info("Sending x to grid dynamics")
            self.sendX(k)
            
            # break apart components of x to send to agents
            log.info("Splitting x")
            self.theta[:, k+1] = self.x[0:self.Nde, k+1]
            self.Pdr[:, k+1] = self.x[(self.Nde):(self.Nde+self.Ndr), k+1];
            self.Pg[:, k+1] = self.x[(self.Nde+self.Ndr):(self.Nde+self.Ndr+self.Ngc), k+1];
            
            self.collection.insert({'k' : k+1, 'pdr' : self.Pdr[:, k+1].tolist()})
            self.collection.insert({'k' : k+1, 'pg' : self.Pg[:, k+1].tolist()})
            
            log.info("Sending Pdr to demand response agents")
            self.sendPdr(k+1)
            
            log.info("Sending Pg to generator agents")
            self.sendPg(k+1)
            
            # line capacity limits (computed at ISO)
            log.info("Computing line capacity limits")
            self.mu5[:, k+1] = np.maximum(0, self.mu5[:, k] + self.Kmu5.dot(-self.B_lineR.dot(self.theta[:, k]) - self.Pmax) )
            self.mu6[:, k+1] = np.maximum(0, self.mu6[:, k] + self.Kmu6.dot(self.B_lineR.dot(self.theta[:, k]) - self.Pmax) )
            
            self.collection.insert({'k' : k+1, 'lpf' : (self.B_lineR.dot(self.theta[:, k])).tolist()})
            
        helpers.exitlog(log, functionName, level=logging.INFO)
            
    def requestGradF(self, k):
        functionName = self.requestGradF.__name__
        helpers.entrylog(log, functionName, locals())
        kwargs = {'method' : 'sendGradF', 'args' : {'k' : k}, 'version' : 1.0}
        msg = MAGIMessage(groups=self.loadGenGroup, docks=self.loadGenDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        log.debug("Sending msg: %s", msg)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    def receiveGradF(self, msg, k, grad_f):
        #log.info("Received X, Source: %s, k:%d, grad_f:%f", msg.src, k, grad_f)
        agentType, agentIndex = msg.src.split("-")
        agentIndex = int(agentIndex)
        if agentType == "dr":
            self.grad_f_current[self.Nde+agentIndex] = grad_f
        elif agentType == "gen":
            self.grad_f_current[self.Nde+self.Ndr+agentIndex] = grad_f
        else:
            log.error("Invalid Agent: %s", msg.src)
        
#     def requestRho(self, k):
#         functionName = self.requestRho.__name__
#         helpers.entrylog(log, functionName, locals(), level=logging.INFO)
#         kwargs = {'method' : 'sendRho', 'args' : {'k' : k}, 'version' : 1.0}
#         msg = MAGIMessage(groups=self.gridDynamicsGroup, docks=self.gridDynamicsDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
#         log.debug("Sending msg: %s", msg)
#         self.messenger.send(msg)
#         helpers.exitlog(log, functionName, level=logging.INFO)
    
    def receiveRho(self, msg, k, rho):
        functionName = self.receiveRho.__name__
        helpers.entrylog(log, functionName)
        log.info("Received rho, k:%d, rho:%f", k, rho)
        self.rho[k] = rho
        helpers.exitlog(log, functionName)
            
    def sendPdr(self, k):
        functionName = self.sendPdr.__name__
        helpers.entrylog(log, functionName)
        
        for agentIndex in range(0, self.Ndr):
            node = "dr-"+str(agentIndex)
            pdr = self.Pdr[agentIndex, k]
            log.debug("Sending Pdr, Node: %s, k:%d, Pdr:%f", node, k, pdr)
            kwargs = {'method' : 'receivePdr', 'args' : {'k' : k, 'pdr' : pdr}, 'version' : 1.0}
            msg = MAGIMessage(nodes=node, docks=self.loadGenDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            
            self.messenger.send(msg)

        helpers.exitlog(log, functionName)
        
    def sendPg(self, k):
        functionName = self.sendPg.__name__
        helpers.entrylog(log, functionName)
        
        for agentIndex in range(0, self.Ngc):
            node = "gen-"+str(agentIndex)
            pg = self.Pg[agentIndex, k]
            log.debug("Sending Pg, Node: %s, k:%d, Pg:%f", node, k, pg)
            kwargs = {'method' : 'receivePg', 'args' : {'k' : k, 'pg' : pg}, 'version' : 1.0}
            msg = MAGIMessage(nodes=node, docks=self.loadGenDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
            self.messenger.send(msg)

        helpers.exitlog(log, functionName)
        
    def sendX(self, k):
        functionName = self.sendX.__name__
        helpers.entrylog(log, functionName)
        x = self.x[:, k]
        kwargs = {'method' : 'receiveX', 'args' : {'k' : k, 'x' : x}, 'version' : 1.0}
        msg = MAGIMessage(groups=self.gridDynamicsGroup, docks=self.gridDynamicsDock, data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
        
    def stopAgent(self, msg):
        functionName = self.stopAgent.__name__
        helpers.entrylog(log, functionName, level=logging.INFO)
        self.active = False
        if self.thread:
            self.thread.join()
        helpers.exitlog(log, functionName, level=logging.INFO)
        

def addColumn(arr, numOfColumns=1):
    arr = np.append(arr, np.zeros((len(arr), numOfColumns)), axis=1)
    return arr

def getAgent(**kwargs):
    agent = ISO()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = ISO()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()