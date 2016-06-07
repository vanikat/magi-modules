#!/usr/bin/env python 

# Copyright (C) 2012 University of Southern California 
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.util.software import requireSoftware
from subprocess import Popen, PIPE, STDOUT
import logging
import sys


class AttackReplay_agent(DispatchAgent):
	"""
	Provides an interface to the tcpreplay utility. 
	"""
	def __init__(self):
		"""Init base class; install required software; setup initial configuration."""
		self.log = logging.getLogger(__name__)
		DispatchAgent.__init__(self)

		#requireSoftware('libpcap-dev')
		#requireSoftware('tcpreplay')  

		self.pids = []

		# 'Basics'
		self.interface = 'eth0' 			# CIDR
		self.pcapfile = None 

	@agentmethod()
	def startattack(self, msg):
		self.log.debug('start() called with msg: %s' % msg)
		self.log.debug('pcap file is %s' % self.pcapfile) 

		cmd=['/usr/local/bin/tcpreplay', '-i']
		cmd.extend([str(self.interface)])
		cmd.extend(['/tmp/attack-mine2chapel.anon'])
		
		self.log.debug('Running cmd: %s' % cmd)
		process = Popen(cmd, stdout=PIPE, shell=False, stderr=STDOUT)
		
		self.log.info('Output from tcpreplay')
		self.log.info(process.communicate())


		return True
	
		## TODO: 
		## Add a confirmConfig and take the pcap file and manage it to change IP,MAC,padding and checksum 

def getAgent():
	agent = AttackReplay_agent()
	return agent

if __name__ == "__main__":
	agent = AttackReplay_agent()
	initializeProcessAgent(agent, sys.argv)
	agent.run()
