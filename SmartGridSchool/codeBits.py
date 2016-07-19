# This code for parsing parameters.conf and creating dictionary for each building
# To be run when each building's function is called by orchestrator (as opposed to args being passed by orchestrator)
def setConfiguration(self, msg, **kwargs):
  with open("parameters.conf") as paramsFile:
    paramsList = paramsFile.read().splitlines()
  self.day = paramList[0][len("day:"):]
  
  
  parameters = open("parameters.conf").splitlines();
  
  
  
  
  
  with open("parameters.conf", r) as parameters:
    from magi.testbed import testbed
    self.hostname = testbed.nodename # should be b-0 to b-21
    for line in parameters:
      if self.hostname in line:
        
      elif "day" in line:
        self.day = line[len("day:"):]
      elif "solarIrradiance" in line:
        self.solarIrradiance = line[len("solarIrradiance:"):]
      elif "panelEff" in line:
        self.panelEff = line[len("panelEff:"):]
