import csv
import sys

class ConfigureScenario(object):
    """
        Loads configuration file
        Writes AAL and TCL to specified path (from user)
        Then experiment AAL/TCL should be run on DETER
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
        with open(vppfn) as vpp_file:
            vpp_reader = csv.reader(vpp_file)
            for i, row in enumerate(vpp_reader):
                if i == 0:
                    # append phony value for at 0 to make timesteps line up
                    vppPower.append(9.999) 
                else:
                    vppPower.append(float(row[1]))
        print repr(vppPower)
        return vppPower

    def loadUnits(self, unitsfn):
        units = []
        with open(unitsfn) as unit_file:
            keys = []
            unit_reader = csv.reader(unit_file)
            for i,row in enumerate(unit_reader):
                if i == 0:
                    for key in row:
                        keys.append(key)
                else:
                    unit = {}
                    for j, val in enumerate(row):
                        unit[keys[j]] = val
                    units.append(unit)
        print "Units: %s" % repr(units)
        return units

    def generateTCL(self, vpp, units, tclfn):
        print "Generating TCL file..."
        num_clients = len(units)
        BASE_TCL_FN = "output/base-tcl.tcl"
        tcl_text = ""
        with open(BASE_TCL_FN) as base_tcl_file:
            tcl_text = base_tcl_file.read()
        with open(tclfn, 'w') as output_tcl_file:
            output_tcl_file.write(tcl_text % num_clients)

    def generateAAL(self, vpp, units, aalfn):
        print "Generating AAL file..."
        num_clients = len(units)
        BASE_AAL_FN = "output/base-aal.aal"
        aal_text = ""
        with open(BASE_AAL_FN) as base_aal_file:
            aal_text = base_aal_file.read()
        with open(aalfn, 'w') as output_aal_file:
            custom_aal = []
            for i in range(len(units)):
                custom_aal.append("clientnode-%d" % i)
            output_aal_file.write(aal_text % ", ".join(custom_aal))

    def generateConfig(self, vpp, units, configfn):
        print "Generating config file..."
        # clean up param names
        # clean up param vals
        # dump json string, tied to nodename


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