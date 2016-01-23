#!/usr/bin/env python

import scipy.io

from magi.util import helpers
from pymongo import MongoClient

import matplotlib.pyplot as plt


def plot(collection, agent, col, val, colRange=None):
    
    records = collection.find({"agent" : agent, col: { "$exists": True }}, {"_id":0, "k":1, col:1}).sort("k")
                  
    x=[]
    y=[]
    
    for rec in records:
        x.append(rec["k"])
        if not colRange:
            y.append(rec[col])
        else:
            y.append(rec[col][colRange[0]:colRange[1]])
    
    plt.plot(x, y)
    
    plt.savefig("/tmp/%s.png" %(val))
    plt.show()
    
    
if __name__ == "__main__":
    
    # Base case config file    
    configFileName = "AGCDR_agent.mat"

    # Variable wind case config file
    #configFileName = "AGCDR_agent_wind.mat"

    config = scipy.io.loadmat(configFileName, mat_dtype=True)
    
    localDbPort = 27020
    dbHost = "control.dmmcont.montage"
    dbPort = 27018

    db_tunnel_cmd = None
    
    try:
        db_tunnel_cmd = helpers.createSSHTunnel('users.deterlab.net', localDbPort, dbHost, dbPort)
        
        c = MongoClient('localhost', localDbPort)
        collection = c['magi']['experiment_data']
        
        plot(collection, "grid_agent", "rho", "rho")
        
        Ndc = int(config['Ndc'])
        Ndr = int(config['Ndr'])
        Ngc = int(config['Ngc'])
        
        # state indices
        w_state = (0, Ndc)
        delta_state = (Ndc, Ndc+Ndc)
        Pc_state = (Ndc+Ndc, Ndc+Ndc+Ndr)
        Pm_state = (Ndc+Ndc+Ndr, Ndc+Ndc+Ndr+Ngc)

        plot(collection, "grid_agent", "y", "frequency", (0, Ndc))

        print("Done")
    
    finally:
        if db_tunnel_cmd:
            helpers.terminateProcess(db_tunnel_cmd)
            
    
    
#     plt.xlabel('samples')
#     plt.ylabel('power')
#     plt.title('BBB')    
#     

#     plot(plt, collection, "pDispatch")
#     plot(plt, collection, "bakeryP")
#     plot(plt, collection, "batteryP")
#     plot(plt, collection, "bucketP")
#     plot(plt, collection, "pResidual")
#     
#     plt.legend(["pDispatch", "bakeryP", "batteryP", "bucketP", "pResidual"], loc='lower right')
#     
#     plt.savefig("/tmp/bbb.png")
#     plt.show()
    

