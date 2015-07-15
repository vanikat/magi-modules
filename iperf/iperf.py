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

class Iperf(DispatchAgent):
	def __init__(self):
		DispatchAgent.__init__(self)
		self.clientFile = '/tmp/iperfClientOutput.txt'
		self.serverFile = '/tmp/iperfServerOutput.txt'
		self.port = 28888
		self.serverProcess = None
		
	@agentmethod()
	def startClient(self, msg, server, port=None, time=10, bw=None):
		functionName = self.startClient.__name__
		helpers.entrylog(log, functionName, locals())
		
		if not server:
			raise AttributeError("iperf server not set")
		
		if port == None:
			port = self.port
		
		iperfCmd = "iperf -c %s -u -p %d -t %d" %(server, port, time)
		if bw:
			iperfCmd = iperfCmd + " -b %d" %port

		log.info("Running: %s" %iperfCmd)
		
		p = Popen(iperfCmd.split(), stdout=PIPE, stderr=PIPE)
		
		if p.wait():
			log.error('Could not start iperf')
			err = p.communicate()[1]
			log.error(err)
			return False
		
		log.info('Successfully running iperf client')
		
		out = p.communicate()[0]
		f = open(self.clientFile, 'w')
		f.write(out)
		f.close()
		
		log.info('iperf client successfully completed')
		return True
		
	@agentmethod()	
	def startServer(self, msg, port=None):
		functionName = self.startServer.__name__
		log.info(locals())
		
		if port == None:
			port = self.port
			
		iperfCmd = "iperf -s -p %d -u" %port
					
		log.info("Running: %s" %iperfCmd)
		
		self.serverProcess = Popen(iperfCmd.split(), stdout=PIPE, stderr=PIPE)
		time.sleep(1)
		
		if self.serverProcess.poll() != None:
			log.info('Could not start iperf')
			raise OSError('could not start iperf server')
		
		log.info('iperf server started with process id %d' %(self.serverProcess.pid))
		
		return True

	@agentmethod()	
	def stopServer(self, msg):
		functionName = self.stopServer.__name__
		helpers.entrylog(log, functionName, locals())
		
		if self.serverProcess:
			self.serverProcess.terminate()
		
		out = self.serverProcess.communicate()[0]
		f = open(self.serverFile, 'w')
		f.write(out)
		f.close()
		
		return True

def getAgent(**kwargs):
	log.info(kwargs)
	agent = Iperf()
	agent.setConfiguration(None, **kwargs)
	return agent
	
if __name__ == "__main__":
	agent = Iperf()
	kwargs = initializeProcessAgent(agent, sys.argv)
	agent.setConfiguration(None, **kwargs)
	agent.run()
