import csv
import sys
import json
import os
import numpy as np
import h5py
from collections import defaultdict

TEMPLATE_DIR = os.path.dirname(os.path.realpath(__file__))

class ConfigureScenario(object):
    """
        Read/writes configuration file
        Writes AAL and TCL and configJSON to specified path (from user)
        Then experiment AAL/TCL/JSON should be run on DETER
        Then compare_results.py should be used to test for accuracy

    """
    def __init__(self):
        pass

    def main(self, configPath, tclfn, aalfn):
        configPath = os.path.abspath(configPath)
        tclfn = os.path.abspath(tclfn)
        aalfn = os.path.abspath(aalfn)
       
        #TODO read these in from file
        self.timeStep = 1.0        
        self.numIterations = 10000 

        self.loadCase(configPath) #sets instance vars
        self.createClientFiles(configPath)
        
        self.numClients = len(self.PdcMax) + len(self.PdtMax) + len(self.PgMax)

        self.generateTCL(tclfn)
        self.generateAAL(aalfn, configPath)

    def loadCase(self, path):

        # todo: remove
        self.caseNum = 30
        self.c = 1
        self.gamma = 0.1
        self.M = 0.1
        self.k = 2
        self.alpha = 0.001
        ###

        fName=path+'/case' + str(self.caseNum) + '.mat'
        inData=h5py.File(fName,'r')
        for name in inData:
            cmd='self.' + name + '=np.transpose(np.array(inData.get(\''+name+'\')))'
            exec(cmd)
        
        state = np.vstack((np.zeros((self.Nde,1)),np.ones((self.Ndc,1)) ,  np.ones((self.Ndt,1)),  np.ones((self.Ng,1)),  np.zeros((self.Nr,1)),  np.zeros((self.Nr,1))))
        
        #self.Hhat=Hhat
        #self.Hhatinv=Hhatinv
        #self.N=N
        #self.m1=m1
        #self.m2=m2
        #self.H=H
        self.state=state
        
        #code.interact(local=locals())
        self.Pdkt=self.Pdk
        Pdkt=self.Pdkt[:,self.k-1]
        self.Pdk=np.expand_dims(Pdkt,1)
        
        self.lastClientUpdate=np.zeros(self.Ndc+self.Ndt+self.Ng)
        self.iterNum=0
        self.df=np.zeros(((self.Ndt+self.Ndc+self.Ng),1))
    
    def createClientFiles(self,path):
        #Ensure case is loaded first
        jsonVals=defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for i in range(0,self.Ndc):
            jsonVals["DC"][str(i)]["PMax"]=self.PdcMax[i][0]
            jsonVals["DC"][str(i)]["PMin"]=self.PdcMin[i][0]
            jsonVals["DC"][str(i)]["b"]=-1*self.bdc[i][0]
            jsonVals["DC"][str(i)]["c"]=-1*self.cdc[i][i]
            jsonVals["DC"][str(i)]["M"]=self.M
        
        for i in range(0,self.Ndt):
            jsonVals["DT"][str(i)]["PMax"]=self.PdtMax[i][0]
            jsonVals["DT"][str(i)]["PMin"]=self.PdtMin[i][0]
            jsonVals["DT"][str(i)]["b"]=-1*self.bdt[i][0]
            jsonVals["DT"][str(i)]["c"]=-1*self.cdt[i][i]
            jsonVals["DT"][str(i)]["M"]=self.M
        
        for i in range(0,self.Ng):
            jsonVals["G"][str(i)]["PMax"]=self.PgMax[i][0]
            jsonVals["G"][str(i)]["PMin"]=self.PgMin[i][0]
            jsonVals["G"][str(i)]["b"]=self.bg[i][0]
            jsonVals["G"][str(i)]["c"]=self.cg[i][i]
            jsonVals["G"][str(i)]["M"]=self.M
            jsonVals["G"][str(i)]["delta"]=self.deltag[i,i]
            jsonVals["G"][str(i)]["gamma"]=self.gamma
        
        fstr = os.path.join(path, 'fullcase.json')
        with open(fstr, 'w') as outFile:
            json.dump(jsonVals, outFile)
        
        nodeAssignment = self.assignNodesToUnits()
        fstr = os.path.join(path, 'nodeAssignment.json')
        with open(fstr, 'w') as outFile:
            json.dump(nodeAssignment, outFile)

    def assignNodesToUnits(self):
        assignment = []

        for i in range(0,self.Ndc):
            assignment.append('DC-'+str(i))

        for i in range(0,self.Ndt):
            assignment.append('DT-'+str(i))

        for i in range(0,self.Ng):
            assignment.append('G-'+str(i))

        return assignment

    def generateTCL(self, tclfn):
        print "Generating TCL file..."
        templateData = {}
        templateData['numClients'] = self.numClients
        tclTemplateFileName = os.path.join(TEMPLATE_DIR, "output/base.tcl")
        tclTemplateText = ""
        with open(tclTemplateFileName) as baseTclFile:
            tclTemplateText = baseTclFile.read()
        with open(tclfn, 'w') as outputTclFile:
            outputTclFile.write(tclTemplateText % templateData)

    def generateAAL(self, aalfn, configPath):
        print "Generating AAL file..."

        templateData = {}
        templateData['configPath'] = configPath
        templateData['clientNodesText'] = ""
        # timeout based on simulation length multipled by some slack factor
        # templateData['timeout'] = self.timeStep * self.numIterations * 1000 * 100000
        templateData['timeout'] = 100000

        aalTemplateFileName = os.path.join(TEMPLATE_DIR, "output/base.aal")
        aalTemplateText = ""
        
        with open(aalTemplateFileName) as baseAalFile:
            aalTemplateText = baseAalFile.read()

        with open(aalfn, 'w') as outputAalFile:
            clientNodes = []
            
            for i in range(self.numClients):
                clientNodes.append("clientnode-%s" % str(i+1))
            templateData['clientNodesText'] = ", ".join(clientNodes)

            outputAalFile.write(aalTemplateText % templateData)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        ConfigureScenario().main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print "Usage: configure_scenario.py configPath tclfn aalfn"