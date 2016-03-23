#!/usr/bin/env python

import logging
from subprocess import Popen, PIPE
import sys

from magi.testbed import testbed
from magi.util import helpers
from magi.util.agent import DispatchAgent
from magi.util.processAgent import initializeProcessAgent

log = logging.getLogger()

class link_up_down(DispatchAgent):
    
    def __init__(self):
        DispatchAgent.__init__(self)

    #there should be a delay node between the two nodes connected by the link for this up/down to work.
    # 'timing' is in seconds - 'timing' is relative to the time the event is called 
    def link_up(self, msg, dest):
        functionName = self.link_up.__name__
        helpers.entrylog(log, functionName, locals())
        
        intf = self.node2Intf(dest)
        
        cmd = "ifconfig %s up" %(intf)
        log.info("Running cmd: %s" %(cmd))
        
        process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        
        if returncode == 0:
            log.info(stdout)
            log.info("Link to node '" + dest + "' brought up.")
        else:
            log.error(stderr)
            log.error("Error in bringing link to node '" + dest + "' up. Error code %d" %(returncode))
        
        return True

    def link_down(self, msg, dest):
        functionName = self.link_down.__name__
        helpers.entrylog(log, functionName, locals())
        
        intf = self.node2Intf(dest)
        
        cmd = "ifconfig %s down" %(intf)
        log.info("Running cmd: %s" %(cmd))
        
        process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        
        if returncode == 0:
                log.info(stdout)
                log.info("Link to node '" + dest + "' put down.")
        else:
                log.error(stderr)
                log.error("Error in putting link to node '" + dest + "' down. Returncode %d" %(returncode))
        
        return True

    def node2Intf(self, dest):
        topoGraph = testbed.getTopoGraph()
        src = testbed.getNodeName()
        linkname = topoGraph[src][dest]['linkName']
        srcLinks = topoGraph.node[src]['links']
        try:
            ip = srcLinks[linkname]['ip']
            return testbed.getInterfaceInfo(ip).name
        except Exception:
            raise Exception("Invalid information. Mostly no direct link to destination '%s'." %(dest))
                  
        
    def link_up_tevc(self, msg, linkName, timing):
        functionName = self.link_up.__name__
        helpers.entrylog(log, functionName, locals())
        
        if timing == 0:
            timing = "now"
        else:
            timing = "+" + str(timing)
        
        cmd = "/usr/testbed/bin/tevc -e %s %s %s up" %(testbed.eid, timing, linkName)
        log.info("Running cmd: %s" %(cmd))
        
        process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        
        if returncode == 0:
            log.info(stdout)
            log.info("Link '" + linkName + "' brought up.")
        else:
            log.error(stderr)
            log.error("Error in bringing link '" + linkName + "' up. Error code %d" %(returncode))
        
        return True

    def link_down_tevc(self, msg, linkName, timing):
        functionName = self.link_down.__name__
        helpers.entrylog(log, functionName, locals())
        
        if timing == 0:
            timing = "now"
        else:
            timing = "+" + str(timing)
        
        cmd = "/usr/testbed/bin/tevc -e %s %s %s down" %(testbed.eid, timing, linkName)
        log.info("Running cmd: %s" %(cmd))
        
        process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        
        if returncode == 0:
                log.info(stdout)
                log.info("Link '" + linkName + "' put down.")
        else:
                log.error(stderr)
                log.error("Error in putting link '" + linkName + "' down. Returncode %d" %(returncode))
        
        return True

# the getAgent() method must be defined somewhere for all agents.
# The Magi daemon invokes this method to get a reference to an
# agent. It uses this reference to run and interact with an agent
# instance.
def getAgent(**kwargs):
    agent = link_up_down()
    agent.setConfiguration(None, **kwargs)
    return agent

# In case the agent is run as a separate process, we need to
# create an instance of the agent, initialize the required
# parameters based on the received arguments, and then call the
# run method defined in DispatchAgent.
if __name__ == "__main__":
    agent = link_up_down()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
