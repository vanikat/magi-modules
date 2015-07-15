#!/usr/bin/env python

# Copyright (C) 2012 University of Southern California
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

import logging
from subprocess import Popen, PIPE
import sys
import time

from magi.util import helpers
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent


log =logging.getLogger(__name__)

class Hping(DispatchAgent):
	def __init__(self):
		DispatchAgent.__init__(self)
		self.process = None
		
	@agentmethod()
	def startHping(self, msg, dest, port=None, interval=None):
		functionName = self.startHping.__name__
		helpers.entrylog(log, functionName, locals())
		
		if not dest:
			raise AttributeError("Destination not set")
		
		hpingCmd = "sudo hping3 %s --udp -q" %dest
		if port:
			hpingCmd = hpingCmd + " -p %d" %port
		if interval:
			hpingCmd = hpingCmd + " -i %d" %interval
		else:
			hpingCmd = hpingCmd + " --flood"
			
		log.info("Running %s" %hpingCmd)
		
		self.process = Popen(hpingCmd.split(), stdout=PIPE, stderr=PIPE)
		time.sleep(1)
		
		if self.process.poll() != None:
			log.error('Could not start hping')
			err = self.process.communicate()[1]
			log.error(err)
			return False
		
		log.info('hping3 started with process id %d' %(self.process.pid))
		return True

	@agentmethod()	
	def stopHping(self, msg):
		log.info("stopping hping3")
		if self.process:
			self.process.terminate()
		return True

def getAgent(**kwargs):
	log.info(kwargs)
	agent = Hping()
	agent.setConfiguration(None, **kwargs)
	return agent
	
if __name__ == "__main__":
	agent = Hping()
	kwargs = initializeProcessAgent(agent, sys.argv)
	agent.setConfiguration(None, **kwargs)
	agent.run()
