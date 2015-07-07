#!/usr/bin/env python
from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

from subprocess import Popen, PIPE
import sys

from magi.testbed import testbed

import logging
log = logging.getLogger()

class Link_up_down(DispatchAgent):
    def __init__(self):
        DispatchAgent.__init__(self)

    #there should be a delay node between the two nodes connected by the link for this up/down to work.
    # 'timing' is in seconds - 'timing' is relative to the time the event is called 
    def link_up(self, msg, link_name, timing):

	proj_exp = testbed.project + "/" + testbed.experiment
	if timing == 0:
		process = Popen(["tevc", "-e", proj_exp, "now", link_name, "up"], stdout=PIPE, stderr=PIPE)
	else:
		timing = "+" + str(timing)
		process = Popen(["tevc", "-e", proj_exp, timing, link_name, "up"], stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        if returncode == 0:
            log.info(stdout)
            log.info("Link: " + link_name + " put up.")
        else:
            log.error(stderr)
            log.error("Error in putting link: " + link_name + " up. Returncode %d" %(returncode))
	return True

     def link_down(self, msg, link_name, timing):
	proj_exp = testbed.project + "/" + testbed.experiment
	if timing == 0:
		process = Popen(["tevc", "-e", proj_exp, "now", link_name, "down"], stdout=PIPE, stderr=PIPE)
	else:
		timing = "+" + str(timing)
		process = Popen(["tevc", "-e", proj_exp, timing, link_name, "down"], stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        if returncode == 0:
            log.info(stdout)
            log.info("Link: " + link_name + " put down.")
        else:
            log.error(stderr)
            log.error("Error in putting link: " + link_name + " down. Returncode %d" %(returncode))
	return True

# the getAgent() method must be defined somewhere for all agents.
# The Magi daemon invokes this method to get a reference to an
# agent. It uses this reference to run and interact with an agent
# instance.
def getAgent():
    agent = Link_up_down()
    return agent

# In case the agent is run as a separate process, we need to
# create an instance of the agent, initialize the required
# parameters based on the received arguments, and then call the
# run method defined in DispatchAgent.
if __name__ == "__main__":
    agent = Link_up_down()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
