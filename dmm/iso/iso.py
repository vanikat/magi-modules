#!/usr/bin/env python

import logging
import scipy.io
import sys
import threading
import time

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import NonBlockingDispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
import yaml

from commServer import ServerCommService
import numpy as np


log = logging.getLogger(__name__)


class ISO(NonBlockingDispatchAgent):
    
    def __init__(self):
        NonBlockingDispatchAgent.__init__(self)
        self.configFileName = 'AGCDR_agent.mat'
        self.loadProfileConfigFileName = 'AGCDR_profiles.mat'
        self.inactiveGenConfigFile = 'AGCDR_agent_remove.mat'
        self.N_iter = 100
        self.thread = None
        self.active = True
        
    def setConfiguration(self, msg, **kwargs):
        NonBlockingDispatchAgent.setConfiguration(self, msg, **kwargs)
        
        log.info("Loading Config File: %s", self.configFileName)
        config = scipy.io.loadmat(self.configFileName, mat_dtype=True)
        self.loadProfileConfig = scipy.io.loadmat(self.loadProfileConfigFileName, mat_dtype=True)
        
        self.N_bus = int(config['N_bus']) # number of buses in the system
        self.N_ang = int(config['N_ang']) # number of voltage angles (excluding slack bus)
        self.N_gen = int(config['N_gen']) # number of (conventional) generators
        self.N_dem = int(config['N_dem']) # number of demand response units (specified by the user and randomly distributed in the grid)
        self.N_line = int(config['N_line']) # number of transmission lines
        self.N_xi = int(config['N_xi']) # number of entries in the xi vector
        
        self.P_L_base = np.squeeze(config['P_L_base'])
        
        self.P_L = np.zeros((len(self.P_L_base), 1))
        self.P_L_hat = np.zeros((len(self.P_L_base), 1))
        
        TotalLoadProfile = self.loadProfileConfig['TotalLoadProfile']
        
        T_start = 0 # Start time in hours (i.e. 8 => 8am)
        duration = 24 # Duration in hours
        
        # Construct P_L and P_L_hat
        index = T_start*3600/2
        scaling_signal = TotalLoadProfile[0,index:index+duration*3600/2]
        initial_magnitude = scaling_signal[0]
        scaling_signal = 1/initial_magnitude*scaling_signal
        #N_iter = len(scaling_signal)
        
        self.P_L = addColumn(self.P_L, self.N_iter-1)
        self.P_L_hat = addColumn(self.P_L_hat, self.N_iter-1)
        
        for k in range(self.N_iter):
            # DETERMINE LOADS FOR THIS TIME INTERVAL
            self.P_L[:,k] = scaling_signal[k]*self.P_L_base
            self.P_L_hat[:,k] = self.P_L_base
        
        self.T_lineR = config['T_lineR']
        self.Nh = config['Nh']
        self.Hbarinv = config['Hbarinv']
        
        self.A1 = config['A1']
        self.A2 = config['A2']
        self.A_G = config['A_G']
        
        self.Pmin = np.squeeze(config['Pmin'])
        self.Pmax = np.squeeze(config['Pmax'])
        self.beta = np.squeeze(config['beta'])
        self.gamma = np.squeeze(config['gamma'])
        
        # gains
        self.alpha = 0.9
        self.Kmu1 = 0.01*np.eye(self.N_line);
        self.Kmu2 = 0.01*np.eye(self.N_line);
        
        self.grad_f = np.zeros((self.N_xi, self.N_iter));
        self.grad_L = np.zeros((self.N_xi, self.N_iter));
        self.lambda_hat = np.zeros((self.N_bus, self.N_iter));
        self.lambda_ = np.zeros((self.N_bus, self.N_iter));
        
        self.grad_f_current = np.zeros((self.N_xi))
        
        self.xi = np.zeros((self.N_xi, self.N_iter+1));
        self.theta = np.zeros((self.N_ang, self.N_iter+1));
        self.P_G = np.zeros((self.N_gen, self.N_iter+1));
        self.P_D = np.zeros((self.N_dem, self.N_iter+1));
        self.inactivePgLoad = np.zeros((self.N_gen,));
        
        self.mu1 = np.zeros((self.N_line, self.N_iter+1));
        self.mu2 = np.zeros((self.N_line, self.N_iter+1));
        
        self.rho = np.zeros((self.N_iter+1, 1));
        
        # Loading stabilized values
        self.xi[:, 0] = config['xi'][:, -1]
        self.mu1[:, 0] = config['mu1'][:, -1]
        self.mu2[:, 0] = config['mu2'][:, -1]
        self.rho[0] = config['rho']
        
        # Splitting components of x
        self.theta[:, 0] = self.xi[0:self.N_ang, 0]
        self.P_G[:, 0] = self.xi[(self.N_ang):(self.N_ang+self.N_gen), 0]
        self.P_D[:, 0] = self.xi[(self.N_ang+self.N_gen):(self.N_ang+self.N_gen+self.N_dem), 0]
        
        self.collection = database.getCollection("iso_agent")
        self.collection.remove({})
        
        # generators removed from the market
        self.inactiveGens = []
        
        # frequency out soft limit or not, managed by grid dynamics agent
        self.freqErrorStatus = False
        
        # how many time-steps ago did the iso last hear from the generators
        self.lastHeardFromGenMap = np.zeros((self.N_gen))
        
        self.commServer = None
    
    @agentmethod()
    def initCommServer(self, msg):
        self.commServer = ServerCommService()
        self.commServer.initCommServer(self.pgResponseHandler)
        
    @agentmethod()
    def stop(self, msg):
        NonBlockingDispatchAgent.stop(self, msg)
        self.commServer.stop()
    
    @agentmethod()
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
            
            self.lastHeardFromGenMap += 1
            
            # break apart components of x to send to agents
            log.info("Splitting x")
            self.theta[:, k] = self.xi[0:self.N_ang, k]
            self.P_G[:, k] = self.xi[(self.N_ang):(self.N_ang+self.N_gen), k];
            self.P_D[:, k] = self.xi[(self.N_ang+self.N_gen):(self.N_ang+self.N_gen+self.N_dem), k];
            
            log.debug("Logging xi (k=%d)", k)
            log.debug(self.xi[:, k])
            
            self.collection.insert({'k' : k, 'pg' : self.P_G[:, k].tolist()})
            self.collection.insert({'k' : k, 'pdr' : self.P_D[:, k].tolist()})
            
            log.info("Sending P_G to generator agents")
            self.sendPg(k)
            
            log.info("Sending P_D to demand response agents")
            self.sendPdr(k)
            
            log.info("Sending theta to grid dynamics")
            self.sendTheta(k)
            
            # voltage angles (computed by ISO)
            log.info("Computing voltage angles")
            self.grad_f_current[0:self.N_ang] = self.T_lineR.conj().transpose().dot(self.mu2[:, k] - self.mu1[:, k])
            
            #TODO: Wait to receive grad_fs, Pg reply and rho
            time.sleep(1) 
            
            self.grad_f[:, k] = self.grad_f_current[:]
            #log.info("Logging grad_f (k=%d)", k)
            #log.info(self.grad_f[:, k])
                
#             if k == 68:
#                 log.info("Removing generator 5")
#                 self.removeGenerator(4, k)
            
            if(self.freqErrorStatus):
                log.info("Frequency Error")
                if ((self.lastHeardFromGenMap > 10).any()):
                    log.info("Communication Error Found")
                    errorGens = np.where(self.lastHeardFromGenMap > 10)[0]
                    for eg in errorGens:
                        self.removeGenerator(eg, k)
            
            log.info("Trimming to active generators only")
            xi_active = self.getActive(self.xi[:, k])
            grad_f_active = self.getActive(self.grad_f[:, k])
            
            #log.info("Logging active xi_active (k=%d)", k)
            #log.info(xi_active)
             
            #log.info("Logging active grad_f (k=%d)", k)
            #log.info(grad_f_active)
            
            log.info("Adjusting exogenous load based on inactive generators")
            self.P_L_hat[:, k] = self.P_L_hat[:, k] - self.A_G.dot(self.inactivePgLoad)
            
            # compute lambda_hat (at ISO)
            log.info("Computing lamda_hat")
            self.lambda_hat[:, k] = self.A1.dot(self.Nh.conj().transpose().dot(xi_active) 
                                                     + self.beta*self.rho[k] + self.P_L_hat[:, k] - self.A2.dot(grad_f_active))
            #log.info(self.lambda_hat[:, k])
            
            # compute prices
            log.info("Computing lambda")
            self.lambda_[:, k] = self.lambda_hat[:, k] - self.alpha*self.gamma*(self.Nh.conj().transpose().dot(xi_active) 
                                                     + self.beta*self.rho[k] + self.P_L_hat[:, k])
            
            #log.info(self.lambda_[:, k])
            self.collection.insert({'k' : k, 'lambda' : self.lambda_[:, k].tolist()})
            
            # compute gradient of Lagrangian (at ISO)
            log.info("Computing gradient of Lagrangian")
            grad_L_active = grad_f_active + self.Nh.dot(self.lambda_hat[:, k])
            
            # update x vector (at ISO, then sent to agents)
            log.info("Updating xi")
            xi_active = xi_active - self.alpha*self.Hbarinv.dot(grad_L_active)
            
            log.info("Expanding to all generators")
            self.xi[:, k+1] = self.getFull(xi_active)
            self.grad_L[:, k] = self.getFull(grad_L_active)
            
            # line capacity limits (computed at ISO)
            log.info("Computing line capacity limits")
            self.mu1[:, k+1] = np.maximum(0, self.mu1[:, k] + self.Kmu1.dot(-self.T_lineR.dot(self.theta[:, k]) + self.Pmin) )
            self.mu2[:, k+1] = np.maximum(0, self.mu2[:, k] + self.Kmu2.dot(self.T_lineR.dot(self.theta[:, k]) - self.Pmax) )
            
            self.collection.insert({'k' : k+1, 'lpf' : (self.T_lineR.dot(self.theta[:, k])).tolist()})
            
        helpers.exitlog(log, functionName, level=logging.INFO)
        
    def sendPg(self, k):
        functionName = self.sendPg.__name__
        helpers.entrylog(log, functionName)
        for agentIndex in range(0, self.N_gen):
            if agentIndex in self.inactiveGens:
                continue
            node = "gen-"+str(agentIndex)
            pg = self.P_G[agentIndex, k]
            log.info("Sending P_G, dst: %s, k:%d, pg:%f", node, k, pg)
            self.commServer.sendData(node, {'k' : k, 'pg' : pg})
        helpers.exitlog(log, functionName)
    
    def sendPdr(self, k):
        functionName = self.sendPdr.__name__
        helpers.entrylog(log, functionName)
        for agentIndex in range(0, self.N_dem):
            node = "dr-"+str(agentIndex)
            pdr = self.P_D[agentIndex, k]
            log.info("Sending P_D, dst: %s, k:%d, pdr:%f", node, k, pdr)
            self.commServer.sendData(node, {'k' : k, 'pdr' : pdr})
        helpers.exitlog(log, functionName)
    
    def sendTheta(self, k):
        functionName = self.sendTheta.__name__
        helpers.entrylog(log, functionName)
        theta = self.theta[:, k]
        kwargs = {'method' : 'receiveTheta', 'args' : {'k' : k, 'theta' : theta}, 'version' : 1.0}
        msg = MAGIMessage(nodes="grid", docks="dmm_dock", data=yaml.dump(kwargs), contenttype=MAGIMessage.YAML)
        self.messenger.send(msg)
        helpers.exitlog(log, functionName)
    
    def pgResponseHandler(self, msgData):
        log.debug("pgResponseHandler:: %s", msgData)
        try:
            src = msgData['src']
            k = msgData['k']
            
            grad_f = msgData['grad_f']
            self.receiveGradF(src, k, grad_f)
            
            if 'pg' in msgData:
                pg = msgData['pg']
                self.receivePgReply(src, k, pg)
        except:
            log.error("Exception while handling response")
    
    def receiveGradF(self, src, k, grad_f):
        log.info("Received grad_f from %s for k=%d: %f", src, k, grad_f)
        agentType, agentIndex = src.split("-")
        agentIndex = int(agentIndex)
        if agentType == "gen":
            self.grad_f_current[self.N_ang+agentIndex] = grad_f
        elif agentType == "dr":
            self.grad_f_current[self.N_ang+self.N_gen+agentIndex] = grad_f
        else:
            log.error("Invalid Agent: %s", src)
    
    def receivePgReply(self, src, k, pg):
        log.debug("Received P_G Reply from %s for k=%d: %f", src, k, pg)
        index = int(src.split("-")[-1])
        self.xi[self.N_ang + index] = pg
        self.lastHeardFromGenMap[index] = 0
        
    @agentmethod()
    def receiveRho(self, msg, k, rho):
        functionName = self.receiveRho.__name__
        helpers.entrylog(log, functionName)
        log.info("Received rho, k:%d, rho:%f", k, rho)
        self.rho[k] = rho
        helpers.exitlog(log, functionName)
    
    @agentmethod()
    def stopAgent(self, msg):
        functionName = self.stopAgent.__name__
        helpers.entrylog(log, functionName, level=logging.INFO)
        self.active = False
        if self.thread:
            self.thread.join()
        helpers.exitlog(log, functionName, level=logging.INFO)
    
    def getActive(self, full):
        active = np.ndarray((0,))
        curItr = 0
        self.inactiveGens.sort()
        for g in self.inactiveGens:
            active = np.concatenate((active, full[curItr:self.N_ang+g]))
            curItr = self.N_ang+g+1
        active = np.concatenate((active, full[curItr:]))
        return active
    
    def getFull(self, active):
        full = np.ndarray((0,))
        curItr = 0
        self.inactiveGens.sort()
        for g in self.inactiveGens:
            full = np.concatenate((full, active[curItr:self.N_ang+g]))
            full = np.concatenate((full, [0]))
            curItr = self.N_ang+g
            #to fix the indexes
            active = np.concatenate(([0], active))
            curItr = curItr+1
        full = np.concatenate((full, active[curItr:]))
        return full
    
    @agentmethod()
    def receiveFreqErrorNotice(self, msg, status):
        log.info("Frequency Error Notice Received: %s" %(status))
        self.freqErrorStatus = status
    
    def removeGenerator(self, genNum, k):
        log.info("Removing generator %d at k:%d" %(genNum, k))
        if genNum in self.inactiveGens:
            log.info("Already Inactive")
            return
        self.inactiveGens.append(genNum)
        self.inactivePgLoad[genNum] = self.P_G[genNum, k]
        config = scipy.io.loadmat(self.inactiveGenConfigFile, mat_dtype=True)
        self.Nh = config['Nh']
        self.Hbarinv = config['Hbarinv']
        self.A1 = config['A1']
        self.A2 = config['A2']
        self.beta = np.squeeze(config['beta'])
    
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
