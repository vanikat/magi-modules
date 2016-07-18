# commented out code: don't know if necessary/not yet implemented
import logging
import math
#import scipy.io
import sys
#import time

from magi.messaging.magimessage import MAGIMessage
from magi.util import helpers, database
from magi.util.agent import NonBlockingDispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
import yaml

class Building(): # difference between DispatchAgent and NonBlockingDispatchAgent?
  def __init__(self):
    DispatchAgent.__init__(self)
    

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
