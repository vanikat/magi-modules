#!/usr/bin/env python

# Copyright (C) 2012 University of Southern California
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

from magi.util.agent import agentmethod, DispatchAgent
from magi.util.processAgent import initializeProcessAgent
from magi.testbed import testbed

from subprocess import Popen
import os
import signal
import sys

import logging

log = logging.getLogger(__name__)

class RuncmdAgent(DispatchAgent):
    '''
    '''
    def __init__(self):
        DispatchAgent.__init__(self)
        self.cmdstring = " " 
        self.pid = None
        
    @agentmethod()
    def start(self, msg):
        log.info("starting ")
        log.info('running: %s', self.cmdstring)
        self.p = Popen([ self.cmdstring ])
        return True
    
    @agentmethod()
    def isDown(self, msg):
        log.info("checking if completed...")
        log.info(self.p.communicate())
        return True
    
def getAgent(**kwargs):
    agent = RuncmdAgent()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = RuncmdAgent()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
