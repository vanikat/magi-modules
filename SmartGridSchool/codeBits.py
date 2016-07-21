# This code for parsing parameters.conf and creating dictionary for each building
# To be run when each building's function is called by orchestrator (as opposed to args being passed by orchestrator)
def setConfiguration(self, msg, **kwargs):
  DispatchAgent.setConfiguration(self, msg, **kwargs)
  
  # create list of strings
  with open("parameters.conf", r) as parameters:
    self.paramsList = paramsFile.read().splitlines()
  
  # define the global parameters
  self.day = paramList[0][len("day:"):]
  self.solarIrradiance = paramList[1][len("solarIrradiance:"):]
  self.panelEff = paramList[2][len("panelEff:"):]
  
  # define the parameters unique to the building
  from magi.testbed import testbed 
  self.hostname = testbed.nodename # should be b-0 to b-21
  index = self.paramsList.index(self.hostname)
  self.area = paramList[index+1][len("area:"):] 
  self.panelArea = paramList[index+2][len("panelArea:"):]
  self.panelTracking = paramList[index+3][len("panelTracking:"):] # boolean: 0 or 1
  self.lights = paramList[index+4][len("lights:"):]
  self.outlets = paramList[index+5][len("outlets:"):]
  self.aapplianceDraw = paramList[index+6][len("applianceDraw:"):]
  self.tempAC = paramList[index+7][len("tempAC:"):]

# To find temperature when given day and timee
# Will most likely be included in the larger AC function
def getTemp(self, msg):
  
