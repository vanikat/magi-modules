import csv
import sys
import json
import os

TEMPLATE_DIR = os.path.dirname(os.path.realpath(__file__))

class ConfigureScenario(object):
    """
        Loads configuration file
        Writes AAL and TCL and configJSON to specified path (from user)
        Then experiment AAL/TCL/JSON should be run on DETER
        Then compare_results.py should be used to test for accuracy

    """
    def __init__(self):
        pass

    def configure(self, vppfn, unitsfn, tclfn, aalfn, configfn):
        tclfn = os.path.abspath(tclfn)
        aalfn = os.path.abspath(aalfn)
        configfn = os.path.abspath(configfn)
        params = self.loadParams(vppfn, unitsfn)
        params["timeStep"] = 1.0
        params["numIterations"] = len(params['vpp'])-1 # -1 for dummy vpp entry
        self.generateTCL(params, tclfn)
        self.generateAAL(params, aalfn, configfn)
    
    def loadParams(self, vppfn, unitsfn):
        vpp = self.loadVPP(vppfn)
        units = self.loadUnits(unitsfn)
        return {"vpp": vpp, "units": units }

    def loadVPP(self, vppfn):
        vppPower = []
        with open(vppfn) as vppFile:
            vppReader = csv.reader(vppFile)
            for i, row in enumerate(vppReader):
                if i == 0:
                    # append phony value for at 0 to make timesteps line up
                    vppPower.append(9.999) 
                else:
                    vppPower.append(float(row[1]))
        print repr(vppPower)
        return vppPower

    def loadUnits(self, unitsfn):
        units = []
        with open(unitsfn) as unitFile:
            canonicalKeys = ["CID", "p", "e", "pMax", "pMin", "eMax", "eMin", "tEnd", "tRun", "type"]
            keys = []
            unitReader = csv.reader(unitFile)
            for i,row in enumerate(unitReader):
                if i == 0:
                    for key in row:
                        keys.append(key)
                    assert "---".join(keys) == "Type-ID---P---E---Pmax---Pmin---Emax---Emin---Tend---Trun", Exception("Error: Input format supplied does not match expected order of Type-ID---P---E---Pmax---Pmin---Emax---Emin---Tend---Trun. Order supplied = %s" % "---".join(keys))
                else:
                    unit = {}
                    for j, val in enumerate(row):
                        unit[canonicalKeys[j]] = val
                    units.append(unit)

                # clean up values from CSV
                for unit in units:
                    unit["type"] = None # will be set below
                    for key in unit:
                        if key == "CID":
                            prefix = unit["CID"][0:3].lower()
                            if  prefix == "bak":
                                unit["type"] = "Bakery"
                            elif prefix == "bat":
                                unit["type"] = "Battery"
                            elif prefix == "bkt":
                                unit["type"] = "Bucket"
                            else:
                                raise Exception, "Unknown unit type prefix: '%s'" % prefix
                        elif key == "type":
                            pass
                        else:
                            unit[key] = float(unit[key])

        print "Units: %s" % repr(units)
        return units

    def generateTCL(self, params, tclfn):
        print "Generating TCL file..."
        templateData = {}
        templateData['numClients'] = len(params['units'])
        tclTemplateFileName = os.path.join(TEMPLATE_DIR, "output/base.tcl")
        tclTemplateText = ""
        with open(tclTemplateFileName) as baseTclFile:
            tclTemplateText = baseTclFile.read()
        with open(tclfn, 'w') as outputTclFile:
            outputTclFile.write(tclTemplateText % templateData)

    def generateAAL(self, params, aalfn, configfn):
        print "Generating AAL file..."
        numClients = len(params['units'])

        templateData = {}
        templateData['configFileName'] = configfn
        templateData['clientNodesText'] = ""
        # timeout based on simulation length multipled by some slack factor
        templateData['timeout'] = params['timeStep'] * params['numIterations'] * 1000 * 100000

        aalTemplateFileName = os.path.join(TEMPLATE_DIR, "output/base.aal")
        aalTemplateText = ""
        
        with open(aalTemplateFileName) as baseAalFile:
            aalTemplateText = baseAalFile.read()

        with open(aalfn, 'w') as outputAalFile:
            clientNodes = []
            
            for i in range(len(params['units'])):
                clientNodes.append("clientnode-%s" % str(i+1))
            templateData['clientNodesText'] = ", ".join(clientNodes)

            outputAalFile.write(aalTemplateText % templateData)

if __name__ == "__main__":
    if len(sys.argv) == 6:
        cs = ConfigureScenario()
        cs.configure(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    else:
        print "Usage: configure_scenario.py vppfile unitfile aalfn tclfn configfn"