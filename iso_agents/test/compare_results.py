import csv
import sys
import yaml

from magi.util.database import getData
from magi.util.helpers import getDBConfigHost
from magi.util import helpers
from magi.db.Server import ROUTER_SERVER_PORT

class CompareResults(object):

    def __init__(self):
        pass

    def test(self, testFn, projectName, expName):
        testData = self.loadTestData(testFn)
        actualData = self.loadActualDataFromDeter(projectName, expName)
        self.compareResults(testData, actualData)

    def loadTestData(self, testFn):
        testData = []

        with open(testFn, 'r') as testFile:
            testDataReader = csv.reader(testFile)
            for i, row in enumerate(testDataReader):
                if i == 0:
                    # skip test data fieldnames in first row of file
                    continue
                else:
                    # Timestep,Residual,Pbak,Pbat,PBkt,VppOut
                    assert len(row) == 6, "Unexpected format for test data!"
                    datum = {}
                    datum["t"] = int(row[0])
                    datum["pResidual"] = float(row[1])
                    datum["bakeryP"] = float(row[2])
                    datum["batteryP"] = float(row[3])
                    datum["bucketP"] = float(row[4])
                    datum["pDispatch"] = float(row[5])
                    testData.append(datum)

        print "TEST DATA:\n%s" % repr(testData)
        return testData

    def loadActualDataFromDeter(self, projectName, expName):
        print "PROJECTNAME: %s, EXPNAME: %s" % (projectName, expName)

        experimentConfigFile = helpers.getExperimentConfigFile(projectName, expName)
        experimentConfig = yaml.load(open(experimentConfigFile, 'r'))
        dbdl = experimentConfig['dbdl']

        data = getData(
            'iso_server_agent', 
            # dbHost=getDBConfigHost(project=projectName, experiment=expName),
            dbHost=helpers.toControlPlaneNodeName(dbdl['configHost']),
            dbPort=ROUTER_SERVER_PORT
        )
        print "ACTUAL RESULTS FROM MONGO:"
        print repr(data)
        return data

    def compareResults(self, testData, actualData):
        testTimeInterval = (testData[0]["t"], testData[-1]["t"])
        filteredData = []
        successes = 0
        failures = 0
        # assuming data is filtered
        for i in range(len(testData)):
            print "Comparing data for timestep %d--------------------------" % testData[i]["t"]
            for k in sorted(testData[i].keys()):
                testValue = testData[i][k]
                if i >= len(actualData):
                    print "Actual data not present for t = %d" % i
                elif actualData[i][k] == testValue:
                    print "%s OK: actual: %s == test: %s" % (k, actualData[i][k], testValue)
                    successes += 1
                else:
                    print "%s FAILED: actual: %s == test: %s" % (k, actualData[i][k], testValue)
                    failures += 1
        
        print "REPORT CARD: %d failures, %d successes, Overall: %f" % (failures, successes, float(successes)/(len(testData)*6))
        


if __name__ == "__main__":
    if len(sys.argv) == 4:
        cr = CompareResults()
        cr.test(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print "Usage: compare_results.py testFn projectName expName"








# Consume testdata file:
#     - For UNIT: 
#         - Test each value (eMin, pForced, etc.) with each step unit history in testdata
#     - For ISO:
#         - Test each value of power Function at each timestep
#         - Test pDispatch for each unit, and all other parameters