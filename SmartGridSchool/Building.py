# TO DO:
# -Implement return time function in Server.py; this will be called by each building at the start of each minute

# commented out code: don't know if necessary/not yet implemented
import logging
import math
#import scipy.io
import sys

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
import yaml

class Building(): # difference between DispatchAgent and NonBlockingDispatchAgent?
    def __init__(self):
    DispatchAgent.__init__(self)
    
    # This code for parsing parameters.conf and creating dictionary for each building
    # To be run when each building's function is called by orchestrator (as opposed to args being passed by orchestrator)
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        
        # create list of strings
        with open("parameters.conf", r) as parameters:
            self.paramsList = paramsFile.read().splitlines()
        
        # define the global parameters
        self.day = paramList[0][len("day:"):]
        self.solarIrradiance = paramList[1][len("solarIrradiance:"):]
        self.panelEff = paramList[2][len("panelEff:"):]
        
        # define the parameters unique to the building
        from magi.testbed import testbed 
        self.hostname = testbed.nodename # should be b-0 to b-21
        index = self.paramsList.index(self.hostname)
        self.area = paramList[index+1][len("area:"):] 
        self.panelArea = paramList[index+2][len("panelArea:"):]
        self.panelTracking = paramList[index+3][len("panelTracking:"):] # boolean: 0 or 1
        self.lights = paramList[index+4][len("lights:"):]
        self.outlets = paramList[index+5][len("outlets:"):]
        self.aapplianceDraw = paramList[index+6][len("applianceDraw:"):]
        self.tempAC = paramList[index+7][len("tempAC:"):]
  
    # electricity generation 
    def generation(self, msg):
        
  
    # electricity consumption
    def consumption(self, msg):
        

# getAgent() method must be defined somewhere for all agents.
# Magi daemon invokes method to get reference to agent. Uses reference to run and interact with agent instance.
def getAgent(**kwargs):
    agent = Building()
    agent.setConfiguration(None, **kwargs)
    return agent

# In case agent run as separate process, need to create instance of agent, initialize required
# parameters based on received arguments, and call run method defined in DispatchAgent.
if __name__ == "__main__":
    agent = Building()
    initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
