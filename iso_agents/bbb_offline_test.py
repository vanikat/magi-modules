import csv
import json
from iso_server_agent.bbb_iso import BBB_ISO

import logging
log = logging.getLogger(__name__)

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
        print "T = %d-----------------------------------------------------------------" % k
        ag = iso.outputAgility()
        for i, u in enumerate(ag["agility"]):
            log.info("%d. %f, %s" % (i, u, ag["cid"][i]))
            print "%d. %f, %s" % (i, u, ag["cid"][i])

    # detailed stats to json
    with open('offline-stats.json', 'w') as jsonFile:
        json.dump(data, jsonFile, indent=4)

    # basic stats to csv
    with open('offline-stats.csv', 'w') as outFile:
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

    for unit in params["units"]:
        with open('longlog/' + unit["CID"] + "-log.csv", 'w') as outFile:
            writer = csv.writer(outFile)
            writer.writerow(["Time", "E", "EMax", "P", "PMax", "PForced", "Agility"])
            for d in data:
                units = d["units"]
                records = [record for record in units if record["CID"] == unit["CID"]]
                assert(len(records)==1)
                record = records[0]
                row = []
                row.append(d["t"])
                row.append(record["e"])
                row.append(record["eMax"])
                row.append(record["p"])
                row.append(record["pMax"])
                row.append(record["pForced"])
                row.append(record["agility"])

                writer.writerow(row)
























if __name__ == "__main__":
    runTest()