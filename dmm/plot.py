#!/usr/bin/env python

import os
import scipy.io
import subprocess

from magi.util import helpers
from pymongo import MongoClient

import matplotlib.pyplot as plt


def plot(collection, agent, col, val, colRange=None, figs_dir="/tmp/"):
    
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
    
    plt.title(val)
    
    plt.savefig(figs_dir + "/%s.png" %(val))
    #plt.show()
    
    plt.close()
    

def plotData(figs_dir, data_file):
    
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
        
        dataImportCmd = "/opt/local/bin/mongoexport --port %d -d magi -c experiment_data --out %s" %(localDbPort, data_file)
        subprocess.call(dataImportCmd, shell=True)
        
        c = MongoClient('localhost', localDbPort)
        collection = c['magi']['experiment_data']
        
        Ndc = int(config['Ndc'])
        Ndr = int(config['Ndr'])
        Ngc = int(config['Ngc'])
        
        # state indices
        w_state = (0, Ndc)
        delta_state = (Ndc, Ndc+Ndc)
        Pc_state = (Ndc+Ndc, Ndc+Ndc+Ndr)
        Pm_state = (Ndc+Ndc+Ndr, Ndc+Ndc+Ndr+Ngc)

        plot(collection, "iso_agent", "lpf", "line_power_flows", None, figs_dir)
        
        plot(collection, "grid_agent", "y", "frequency_fluctuation", w_state, figs_dir)
        plot(collection, "grid_agent", "y", "voltage_angles", delta_state, figs_dir)
        
        plot(collection, "iso_agent", "pdr", "consumption_commanded", None, figs_dir)
        plot(collection, "grid_agent", "y", "consumption_actual", Pc_state, figs_dir)
        
        plot(collection, "grid_agent", "edr", "consumption_energy", None, figs_dir)
        
        plot(collection, "iso_agent", "pg", "generation_commanded", None, figs_dir)
        plot(collection, "grid_agent", "y", "generation_actual", Pm_state, figs_dir)
        
        plot(collection, "grid_agent", "rho", "rho", None, figs_dir)

    
    finally:
        if db_tunnel_cmd:
            helpers.terminateProcess(db_tunnel_cmd)
            

if __name__ == "__main__":
    
    aalFile = "/Users/jaipuria/playground/deter/magi-modules/dmm/outage2.aal"
    aal = helpers.loadYaml(aalFile)
    
    data_dir = "/Users/jaipuria/playground/cps/dmm_figs/data/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
            
    for n in [10, 30, 54]:
        
        outageGrp = []
        for itr in range(n):
            outageGrp.append("gen-%d" %(itr))
             
        aal['eventstreams']['grid_stream'][3]['agent'] = "gen_agent"
        aal['eventstreams']['grid_stream'][3]['args']['nodes'] = outageGrp
         
        aal['eventstreams']['grid_stream'][5]['agent'] = "gen_agent"
        aal['eventstreams']['grid_stream'][5]['args']['nodes'] = outageGrp
         
        helpers.writeYaml(aal, aalFile)
         
        orchCmd = "/usr/local/bin/magi_orchestrator.py -b localhost -f %s" %(aalFile)
        subprocess.call(orchCmd, shell=True)
             
        figs_dir = "/Users/jaipuria/playground/cps/dmm_figs/case2_gen_%d/" %(n)
        if not os.path.exists(figs_dir):
            os.makedirs(figs_dir)
         
        data_file = data_dir + "magi_experiment_data_case2_gen_%d.json" %(n)
        
        plotData(figs_dir, data_file)    
    
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
    

