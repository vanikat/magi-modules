# This code for parsing parameters.conf and creating dictionary for each building
# To be run when each building's function is called by orchestrator (as opposed to args being passed by orchestrator)
def setConfiguration(self, msg, **kwargs):
  with open("parameters.conf", r) as parameters:
    from magi.testbed import testbed
    self.hostname = testbed.nodename # should be b-0 to b-21
    for line in parameters:
      
