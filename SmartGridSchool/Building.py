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

from CommClient import ClientCommService

log = logging.getLogger(__name__)

class Building(DispatchAgent): # difference between DispatchAgent and NonBlockingDispatchAgent?
    def __init__(self):
        DispatchAgent.__init__(self)
        
        #Default arguments for server and clientId:
        self.server = 'localhost'
        self.clientId = None
    
    # This code for parsing parameters.conf
    def setConfiguration(self, msg, **kwargs):
        DispatchAgent.setConfiguration(self, msg, **kwargs)
        
        '''From simple_client > client.py'''
        from magi.testbed import testbed
        if self.clientId == None:
            self.hostname = testbed.nodename # should be b-0 to b-21
            log.info("Hostname: %s", self.hostname)
            self.clientId = self.hostname
        
        # The clientId can be set programmatically to append the hostname .
        self.setClientid() 
        self.commClient = None
        
        '''Parsing for Parameters'''
        # create list of strings
        with open("/users/rning/magi-modules/SmartGridSchool/Parameters.conf", "r") as parameters:
            self.paramsList = paramsFile.read().splitlines()
        
        # define the global parameters
        self.day = paramList[0][len("day:"):]
        self.solarIrradiance = paramList[1][len("solarIrradiance:"):]
        self.panelEff = paramList[2][len("panelEff:"):]
        
        # define the parameters unique to the building
        ## from magi.testbed import testbed 
        ## self.hostname = testbed.nodename # should be b-0 to b-21
        index = self.paramsList.index(self.hostname)
        self.area = paramList[index+1][len("area:"):] 
        self.panelArea = paramList[index+2][len("panelArea:"):]
        self.panelTracking = paramList[index+3][len("panelTracking:"):] # boolean: 0 or 1
        self.lights = paramList[index+4][len("lights:"):]
        self.outlets = paramList[index+5][len("outlets:"):]
        self.aapplianceDraw = paramList[index+6][len("applianceDraw:"):]
        self.tempAC = paramList[index+7][len("tempAC:"):]
    
    # From simple_client > client.py
    def setClientid(self):
    # The method is called in the setConfiguration to set a unique clientID  for the client in a group 
    # If there is only one client per host, then the clientId can be the hostname 
    # but if there are more than one clients per host, we will need to add a random int to it... 
        return
    
    # From simple_client > client.py
    @agentmethod()
    def startclient(self, msg):
        self.commClient = ClientCommService(self.clientId)
        self.commClient.initCommClient(self.server, self.requestHandler)
    
    # From simple_client > client.py
    @agentmethod()
    def stopclient(self, msg):
        DispatchAgent.stop(self, msg)
        if self.commClient:
            self.commClient.stop()
    
    # From simple_client > client.py
    def requestHandler(self, msgData):
        log.info("RequestHandler: %s", msgData)
        
        dst = msgData['dst']
        if dst != self.hostname:
            log.error("Message sent to incorrect destination.")
            return
        
        src= msgData['src']
        string = msgData['string']
        
        log.info("src and string: %s %s", src, string)
    
    # electricity generation 
    #def generation(self, msg):
        #
  
    # electricity consumption
    #def consumption(self, msg):
        #    

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
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
