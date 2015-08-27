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


    # def loadCase(self,path):
    #     fName=path+'/case' + str(self.caseNum) + '.mat'
    #     inData=h5py.File(fName,'r')
    #     for name in inData:
    #         cmd='self.' + name + '=np.transpose(np.array(inData.get(\''+name+'\')))'
    #         exec(cmd)
        
    #     '''
    #     #Removed to import instead of inverse calc
    #     H11=np.zeros((self.Nde,self.Nde))
    #     H12=np.zeros((self.Nde,self.Ndc))
    #     H13=np.zeros((self.Nde,self.Ndt))
    #     H14=np.zeros((self.Nde,self.Ng))

    #     H21=np.transpose(H12)
    #     H22=np.eye(self.Ndc[0][0].astype(int))
    #     H23=np.zeros((self.Ndc,self.Ndt))
    #     H24=np.zeros((self.Ndc,self.Ng))

    #     H31=np.transpose(H13)
    #     H32=np.transpose(H23)
    #     H33=np.eye(self.Ndt[0][0].astype(int))
    #     H34=np.zeros((self.Ndt,self.Ng))
        
    #     H41=np.transpose(H14)
    #     H42=np.transpose(H24)
    #     H43=np.transpose(H34)
    #     H44=np.eye(self.Ng[0][0].astype(int))
        
    #     H1=np.hstack((H11,H12,H13,H14))
    #     H2=np.hstack((H21,H22,H23,H24))
    #     H3=np.hstack((H31,H32,H33,H34))
    #     H4=np.hstack((H41,H42,H43,H44))
    #     H=np.vstack((H1,H2,H3,H4))
        
    #     N=np.hstack((np.transpose(self.BnmSumR),np.transpose(self.Adc),np.transpose(self.Adt),-1*np.transpose(self.Ag)))
    #     N=np.transpose(N)
        
    #     Hhat=H+np.dot(np.dot(self.c,N),np.transpose(N))
    #     Hhatinv=scipy.linalg.inv(Hhat)
    #     m1=scipy.linalg.inv(np.dot(np.dot(np.transpose(N),Hhatinv),N))
    #     m2=np.dot(np.transpose(N),Hhatinv)
    #     '''
    #     state = np.vstack((np.zeros((self.Nde,1)),np.ones((self.Ndc,1)) ,  np.ones((self.Ndt,1)),  np.ones((self.Ng,1)),  np.zeros((self.Nr,1)),  np.zeros((self.Nr,1))))
        
    #     #self.Hhat=Hhat
    #     #self.Hhatinv=Hhatinv
    #     #self.N=N
    #     #self.m1=m1
    #     #self.m2=m2
    #     #self.H=H
    #     self.state=state
        
    #     #code.interact(local=locals())
    #     self.Pdkt=self.Pdk
    #     Pdkt=self.Pdkt[:,self.k-1]
    #     self.Pdk=np.expand_dims(Pdkt,1)
        
    #     self.lastClientUpdate=np.zeros(self.Ndc+self.Ndt+self.Ng)
    #     self.iterNum=0
    #     self.df=np.zeros(((self.Ndt+self.Ndc+self.Ng),1))
    
    # def createClientFiles(self,path):
    #     #Ensure case is loaded first
    #     jsonVals=defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        
    #     for i in range(0,self.Ndc):
    #         jsonVals["DC"][str(i)]["PMax"]=self.PdcMax[i][0]
    #         jsonVals["DC"][str(i)]["PMin"]=self.PdcMin[i][0]
    #         jsonVals["DC"][str(i)]["b"]=-1*self.bdc[i][0]
    #         jsonVals["DC"][str(i)]["c"]=-1*self.cdc[i][i]
    #         jsonVals["DC"][str(i)]["M"]=self.M
        
    #     for i in range(0,self.Ndt):
    #         jsonVals["DT"][str(i)]["PMax"]=self.PdtMax[i][0]
    #         jsonVals["DT"][str(i)]["PMin"]=self.PdtMin[i][0]
    #         jsonVals["DT"][str(i)]["b"]=-1*self.bdt[i][0]
    #         jsonVals["DT"][str(i)]["c"]=-1*self.cdt[i][i]
    #         jsonVals["DT"][str(i)]["M"]=self.M
        
    #     for i in range(0,self.Ng):
    #         jsonVals["G"][str(i)]["PMax"]=self.PgMax[i][0]
    #         jsonVals["G"][str(i)]["PMin"]=self.PgMin[i][0]
    #         jsonVals["G"][str(i)]["b"]=self.bg[i][0]
    #         jsonVals["G"][str(i)]["c"]=self.cg[i][i]
    #         jsonVals["G"][str(i)]["M"]=self.M
    #         jsonVals["G"][str(i)]["delta"]=self.deltag[i,i]
    #         jsonVals["G"][str(i)]["gamma"]=self.gamma
        
    #     fstr=path + '/fullcase.json'
    #     f=open(fstr,'w')
    #     f.write(json.dumps(jsonVals))
    #     f.flush()
    #     f.close()
        
    #     #determine client-node assignments
    #     numNodes=1
    #     jsonVals=defaultdict(lambda: defaultdict(list))
        
    #     for i in range(0,numNodes):
    #         nodeName='nodeIsoClient-' + str(i+1)
    #         numDc=self.Ndc
    #         numDt=self.Ndt
    #         numG=self.Ng
    #         idx=0;
    #         for k in range(0,numDc):
    #             jsonVals[nodeName][str(idx)]='DC,'+str(k)
    #             idx += 1
    #         for k in range(0,numDt):
    #             jsonVals[nodeName][str(idx)]='DT,'+str(k)
    #             idx += 1
    #         for k in range(0,numG):
    #             jsonVals[nodeName][str(idx)]='G,'+str(k)
    #             idx += 1
        
    #     fstr=path + '/clientAssignment.json'
    #     f=open(fstr,'w')
    #     f.write(json.dumps(jsonVals))
    #     f.flush()
    #     f.close()
        
        
    #     cl=self.getClientList()
    #     fstr=path+'/clist.txt'
    #     f=open(fstr,'w')
    #     f.write(json.dumps(cl))
    #     f.flush()
    #     f.close()
        
    def configure(self, vppfn, unitsfn, tclfn, aalfn, configfn):
        tclfn = os.path.abspath(tclfn)
        aalfn = os.path.abspath(aalfn)
        configfn = os.path.abspath(configfn)
        params = self.loadParams(vppfn, unitsfn)
        params["timeStep"] = 1.0
        params["numIterations"] = len(params['vpp'])-1 # -1 for dummy vpp entry
        self.generateConfig(params, configfn)
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

    def generateConfig(self, params, configfn):
        print "Generating config file..."
        params["units"].sort(key=lambda u: int(u['CID'].split("-")[1]))
        with open(configfn, 'w') as configFile:
            json.dump(params, configFile, sort_keys=True, indent=4, ensure_ascii=False)
        return params

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