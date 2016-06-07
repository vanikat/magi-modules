#!/usr/bin/env python

import os
import scipy.io

from magi.util import helpers
from pymongo import MongoClient

import matplotlib.pyplot as plt

def plot(collection, agent, col, title, output=None, colRange=None, figs_dir="/tmp/"):
    
    records = collection.find({"agent" : agent, col: { "$exists": True }}, {"_id":0, "k":1, col:1}).sort("k")
                  
    x=[]
    y=[]
    
    for rec in records[0:]:
        x.append(rec["k"])
        if colRange is None:
            y.append(rec[col])
        else:
            y.append(rec[col][colRange[0]:colRange[1]])
    
    plt.plot(x, y)
    
    ax = plt.gca()
    ax.get_yaxis().get_major_formatter().set_useOffset(False)

    plt.title(title)
    
    if output is None:
        output = title
        
    plt.savefig(figs_dir + "/%s.png" %(output))
    #plt.show()
    
    plt.close()
    

def plotData(figs_dir, data_file):
    
    # Base case config file    
    configFileName = "AGCDR_agent_revised.mat"

    # Variable wind case config file
    #configFileName = "AGCDR_agent_wind.mat"

    config = scipy.io.loadmat(configFileName, mat_dtype=True)
    
    localDbPort = 27020
    dbHost = "control.dmmcont.montage"
    dbPort = 27018

    db_tunnel_cmd = None
    
    try:
        db_tunnel_cmd = helpers.createSSHTunnel('users.deterlab.net', localDbPort, dbHost, dbPort)
        
#         dataImportCmd = "/opt/local/bin/mongoexport --port %d -d magi -c experiment_data --out %s" %(localDbPort, data_file)
#         subprocess.call(dataImportCmd, shell=True)
        
        c = MongoClient('localhost', localDbPort)
        collection = c['magi']['experiment_data']
        
        # state indices
        w_state = config['w_state'].astype(int)-1
        delta_state = config['delta_state'].astype(int)-1
        Pc_state = config['Pc_state'].astype(int)-1
        Pm_state = config['Pm_state'].astype(int)-1
        
        w_state = ((w_state).min(), (w_state).max())
        delta_state = ((delta_state).min(), (delta_state).max())
        Pc_state = ((Pc_state).min(), (Pc_state).max())
        Pm_state = ((Pm_state).min(), (Pm_state).max())

        plot(collection, "iso_agent", "lpf", "Line Power Flows", "lpf", None, figs_dir)
        plot(collection, "iso_agent", "lambda", "LMPs [per MW]", "lmp", None, figs_dir)
        
        plot(collection, "grid_agent", "y", "Bus Frequencies", "frequency", w_state, figs_dir)
        plot(collection, "grid_agent", "y", "Voltage Angles", "voltage_angles", delta_state, figs_dir)
        
        plot(collection, "iso_agent", "pdr", "Commanded Consumption", "consumption_commanded", None, figs_dir)
        plot(collection, "grid_agent", "y", "Actual Consumption", "consumption_actual", Pc_state, figs_dir)
        
        plot(collection, "grid_agent", "edr", "Energy Consumption", "edr", None, figs_dir)
        
        plot(collection, "iso_agent", "pg", "Commanded Generation", "generation_commanded", None, figs_dir)
        plot(collection, "grid_agent", "y", "Actual Generation", "generation_actual", Pm_state, figs_dir)
        
        plot(collection, "grid_agent", "rho", "Rho", "rho", None, figs_dir)
        
        plot(collection, "iso_agent", "grad_f", "Grad_f", "grad_f", None, figs_dir)
        plot(collection, "iso_agent", "gppu", "Generator Power Price Per Unit", "gppu", None, figs_dir)
        plot(collection, "iso_agent", "gtpc", "Generator Total Power Cost", "gtpc", None, figs_dir)
        
        plot(collection, "iso_agent", "tpc", "Total Power Cost", "tpc", None, figs_dir)
        plot(collection, "iso_agent", "appu", "Average Power Price Per Unit / Social Welfare", "appu", None, figs_dir)
        
        plot(collection, "iso_agent", "tpg", "Total Power Generated", "tpg", None, figs_dir)
    
    finally:
        if db_tunnel_cmd:
            helpers.terminateProcess(db_tunnel_cmd)
            

if __name__ == "__main__":
    
#     aalFile = "/Users/jaipuria/playground/deter/magi-modules/dmm/outage2.aal"
#     aal = helpers.loadYaml(aalFile)
    
    data_dir = "/Users/jaipuria/playground/cps/dmm_figs/data/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
            
#     for n in [10, 30, 54]:
#         
#         outageGrp = []
#         for itr in range(n):
#             outageGrp.append("gen-%d" %(itr))
#              
#         aal['eventstreams']['grid_stream'][3]['agent'] = "gen_agent"
#         aal['eventstreams']['grid_stream'][3]['args']['nodes'] = outageGrp
#          
#         aal['eventstreams']['grid_stream'][5]['agent'] = "gen_agent"
#         aal['eventstreams']['grid_stream'][5]['args']['nodes'] = outageGrp
#          
#         helpers.writeYaml(aal, aalFile)
#          
#         orchCmd = "/usr/local/bin/magi_orchestrator.py -b localhost -f %s" %(aalFile)
#         subprocess.call(orchCmd, shell=True)
#              
#         figs_dir = "/Users/jaipuria/playground/cps/dmm_figs/case2_gen_%d/" %(n)
#         if not os.path.exists(figs_dir):
#             os.makedirs(figs_dir)
#          
#         data_file = data_dir + "magi_experiment_data_case2_gen_%d.json" %(n)
#         
#         plotData(figs_dir, data_file)    
    
    figs_dir = "/Users/jaipuria/playground/cps/dmm_figs/attack_new/temp_0/"
    if not os.path.exists(figs_dir):
        os.makedirs(figs_dir)
    
    data_file = data_dir + "magi_experiment_data_attack_new.json"
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
    
    print "Done."

