import csv
import sys
import simplejson as json

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
        vpp, units = self.loadParams(vppfn, unitsfn)
        self.generateTCL(vpp, units, tclfn)
        self.generateAAL(vpp, units, aalfn)
        self.generateConfig(vpp, units, configfn)
    
    def loadParams(self, vppfn, unitsfn):
        vpp = self.loadVPP(vppfn)
        units = self.loadUnits(unitsfn)
        return vpp, units

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
                                unit["type"] = "Bakery"
                            else:
                                raise Exception, "Unknown unit type prefix: '%s'" % prefix
                        elif key == "type":
                            pass
                        else:
                            unit[key] = float(unit[key])

        print "Units: %s" % repr(units)
        return units

    def generateTCL(self, vpp, units, tclfn):
        print "Generating TCL file..."
        numClients = len(units)
        BASE_TCL_FN = "output/base-tcl.tcl"
        tclText = ""
        with open(BASE_TCL_FN) as baseTclFile:
            tclText = baseTclFile.read()
        with open(tclfn, 'w') as outputTclFile:
            outputTclFile.write(tcl_text % numClients)

    def generateAAL(self, vpp, units, aalfn):
        print "Generating AAL file..."
        numClients = len(units)
        BASE_AAL_FN = "output/base-aal.aal"
        aalText = ""
        with open(BASE_AAL_FN) as baseAalFile:
            aalText = baseAalFile.read()
        with open(aalfn, 'w') as outputAalFile:
            customAal = []
            for i in range(len(units)):
                customAal.append("clientnode-%d" % i)
            outputAalFile.write(aalText % ", ".join(customAal))

    def generateConfig(self, vpp, units, configfn):
        print "Generating config file..."
        params = {}
        params["vpp"] = vpp
        params["units"] = units
        params["timeStep"] = 1.0
        with open(configfn, 'w') as configFile:
            configFile.write(json.dumps(params))


# CLient / Server changes:
    #  Agents fully parameterized through MAGI
    #  data should be tagged with some exp #
    #  Remove references to agileBalancing / BBB (should be able to use any algorithm)




# Consume config file:
#     - Read from CSV to get each agent
#     - Read from CSV file to get VPP power function
#         - Load the vpp power history into a list and wrap it with a pDispatch function


if __name__ == "__main__":
    if len(sys.argv) == 6:
        cs = ConfigureScenario()
        cs.configure(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    else:
        print "Usage: configure_scenario.py vppfile unitfile aalfn tclfn configfn"