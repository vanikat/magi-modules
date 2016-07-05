#!/usr/bin/env python

# Copyright (C) 2012 University of Southern California
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

import logging
import sys

from magi.util import database, helpers
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent


log = logging.getLogger(__name__)

class Agent101(DispatchAgent):
    """
            Illustrates how methds can be developed for agents in MAGI 
	"""
    def __init__(self):
        DispatchAgent.__init__(self)
        
    @agentmethod() 
    def testChar(self, msg, a, b):
        functionName = self.testChar.__name__
        helpers.entrylog(log, functionName, locals(), logging.INFO)
        log.info("a: %s" %(a))
        log.info("b: %s" %(b))
        result = a + b
        log.info("result: %s" %(result))
        helpers.exitlog(log, functionName, result, logging.INFO)
        return result
    
    @agentmethod() 
    def testInt(self, msg, a, b):
        functionName = self.testInt.__name__
        helpers.entrylog(log, functionName, locals(), logging.INFO)
        log.info("a: %d" %(a))
        log.info("b: %d" %(b))
        result = a + b
        log.info("result: %d" %(result))
        helpers.exitlog(log, functionName, result, logging.INFO)
        return result
    
    @agentmethod() 
    def testVoid(self, msg):
        functionName = self.testVoid.__name__
        helpers.entrylog(log, functionName, locals(), logging.INFO)
        collection = database.getCollection(self.name)
        collection.insert({"function" : "testVoid"})
        helpers.exitlog(log, functionName, None, logging.INFO)
    
def getAgent(**kwargs):
    agent = Agent101()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = Agent101()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
