import csv
import json
from iso_server_agent.bbb_iso import BBB_ISO

def runTest():
    params = {}
    with open('config/output/star105.json', 'r') as configFile:
        params = json.load(configFile)

    data = []
    
    iso = BBB_ISO()
    for unit in params["units"]:
        iso.registerClient(unit["CID"], unit)
    
    for k in range(1, params["numIterations"]+1):
        iso.agileBalancing(k, params["vpp"][k])
        data.append(iso.generateStats(k, params["vpp"][k]))

    with open('offline-test-2.csv', 'w') as outFile:
        writer = csv.writer(outFile)
        
        keys = ['Timestep','Residual','Pbak','Pbat','PBkt','VppOut']
        writer.writerow(keys)
        
        for d in data:
            output = []
            
            output.append(d["t"])
            output.append(d["pResidual"])
            output.append(d["bakeryP"])
            output.append(d["batteryP"])
            output.append(d["bucketP"])
            output.append(d["pDispatch"])

            writer.writerow(output)


if __name__ == "__main__":
    runTest()