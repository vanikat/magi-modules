#!/usr/bin/env python

# Copyright (C) 2012 University of Southern California
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

import subprocess
import logging
import sys

log = logging.getLogger(__name__)

class RunShell(DispatchAgent):
    """
            Runs the specified script in a shell 
	"""
    def __init__(self):
        DispatchAgent.__init__(self)
        self.path = ''
        
    @agentmethod() 
    def execute(self, msg):
        cmd = [str(self.path)]
        log.info('Running cmd: %s' % cmd)
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()[0]
        log.info('Output: ' + output)
        return True

def getAgent(**kwargs):
    agent = RunShell()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = RunShell()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
