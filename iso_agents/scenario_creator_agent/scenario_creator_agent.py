from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent

import logging
log = logging.getLogger(__name__)

class ScenarioCreatorAgent(DispatchAgent):

    def __init__(self):
        DispatchAgent.__init__(self)
        self.filename = 'tmp-scenario.json'

    @agentmethod()
    def createScenario(self, msg):
        log.info("Creating scenario at %s" % self.filename)
        open(self.filename, 'w').close()
        return True

    @agentmethod()
    def releaseScenario(self, msg):
        log.info("Ending scenario...")
        return True

def getAgent(**kwargs):
    agent = ScenarioCreatorAgent()
    agent.setConfiguration(None, **kwargs)
    return agent