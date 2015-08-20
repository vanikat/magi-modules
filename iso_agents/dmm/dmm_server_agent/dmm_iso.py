import numpy as np
import scipy as sp
import scipy.io as spio
import scipy.linalg
import h5py
#For interactive keyboard breaks
import code
import json
import csv
from collections import defaultdict

"""
DISO.createClientFiles('/proj/cmregx/exp/smalldmmcmrex/expdata')

#Use this to test
from DMM_ISO import DMM_ISO
DISO=DMM_ISO('/proj/cmregx/exp/smalldmmcmrex/expdata',30,1,0.1,0.1,2,0.001)
DISO.runTest('/proj/cmregx/exp/smalldmmcmrex/expdata/iso_server/dmmtest.csv',10000)

for i in range(0, 1000):
    df=DISO.UpdateUtil()
    DISO.UpdateState(df)

"""

class DMM_ISO:
    
    def runTest(self,file,iterations):
        f=open(file,'wt')
        writer=csv.writer(f)
        for i in range(0,iterations):
            df=self.UpdateUtil()
            self.UpdateState(df)
            state=self.getStateData()
            if (i+1)%10==0:
                writer.writerow(state)
                print 'Completed iteration ' + str(i)
        pass
    
    def loadCase(self,path):
        fName=path+'/case' + str(self.caseNum) + '.mat'
        inData=h5py.File(fName,'r')
        for name in inData:
            cmd='self.' + name + '=np.transpose(np.array(inData.get(\''+name+'\')))'
            exec(cmd)
        
        '''
        #Removed to import instead of inverse calc
        H11=np.zeros((self.Nde,self.Nde))
        H12=np.zeros((self.Nde,self.Ndc))
        H13=np.zeros((self.Nde,self.Ndt))
        H14=np.zeros((self.Nde,self.Ng))

        H21=np.transpose(H12)
        H22=np.eye(self.Ndc[0][0].astype(int))
        H23=np.zeros((self.Ndc,self.Ndt))
        H24=np.zeros((self.Ndc,self.Ng))

        H31=np.transpose(H13)
        H32=np.transpose(H23)
        H33=np.eye(self.Ndt[0][0].astype(int))
        H34=np.zeros((self.Ndt,self.Ng))
        
        H41=np.transpose(H14)
        H42=np.transpose(H24)
        H43=np.transpose(H34)
        H44=np.eye(self.Ng[0][0].astype(int))
        
        H1=np.hstack((H11,H12,H13,H14))
        H2=np.hstack((H21,H22,H23,H24))
        H3=np.hstack((H31,H32,H33,H34))
        H4=np.hstack((H41,H42,H43,H44))
        H=np.vstack((H1,H2,H3,H4))
        
        N=np.hstack((np.transpose(self.BnmSumR),np.transpose(self.Adc),np.transpose(self.Adt),-1*np.transpose(self.Ag)))
        N=np.transpose(N)
        
        Hhat=H+np.dot(np.dot(self.c,N),np.transpose(N))
        Hhatinv=scipy.linalg.inv(Hhat)
        m1=scipy.linalg.inv(np.dot(np.dot(np.transpose(N),Hhatinv),N))
        m2=np.dot(np.transpose(N),Hhatinv)
        '''
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
        
    
    def UpdateUtil(self):
        deltaState = np.arange(0,self.Nde).astype(int)
        PdcState = np.arange(self.Nde,self.Nde+self.Ndc).astype(int)
        PdtState = np.arange(self.Nde+self.Ndc,self.Nde+self.Ndc+self.Ndt).astype(int)
        PgState = np.arange(self.Nde+self.Ndc+self.Ndt,self.Nde+self.Ndc+self.Ndt+self.Ng).astype(int)
        lambdaState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr).astype(int)
        lambdahatState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr).astype(int)
        PdkState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr+self.Ndk).astype(int)

        PgMaxk=np.zeros((self.Ng,1))
        PgMaxf=np.zeros((self.Ng,1))

        #for i in range(0, self.Ng):
        #   PgMaxf[i]=self.PgMax[i][0]*(1+(self.deltag[i,i]/100.0))

        #for i in range(0, self.Ng):
        #   PgMaxk[i]=PgMaxk[i]-np.minimum((PgMaxk[i]-self.state[PgState[i]])*self.gamma,PgMaxk[i]-PgMaxf[i])

        '''
        df=np.vstack((-np.transpose(self.bdc)-np.dot(self.cdc,self.state[PdcState]),-np.transpose(self.bdt)-np.dot(self.cdt,self.state[PdtState] ),np.transpose(self.bg)+np.dot(self.cg,self.state[PgState])))

        T1=self.M/(self.state[PdcState]-np.transpose(self.PdcMax))**2-self.M/(self.state[PdcState]-np.transpose(self.PdcMin))**2
        T2=self.M/(self.state[PdtState]-np.transpose(self.PdtMax))**2-self.M/(self.state[PdtState]-np.transpose(self.PdtMin))**2
        T3=self.M/(self.state[PgState]-np.transpose(self.PgMax))**2-self.M/(self.state[PgState]-np.transpose(self.PgMin))**2
        T=np.vstack((T1,T2,T3))
        '''
        
        df=np.vstack((-(self.bdc)-np.dot(self.cdc,self.state[PdcState]),-(self.bdt)-np.dot(self.cdt,self.state[PdtState] ),(self.bg)+np.dot(self.cg,self.state[PgState])))

        T1=self.M/(self.state[PdcState]-(self.PdcMax))**2-self.M/(self.state[PdcState]-(self.PdcMin))**2
        T2=self.M/(self.state[PdtState]-(self.PdtMax))**2-self.M/(self.state[PdtState]-(self.PdtMin))**2
        T3=self.M/(self.state[PgState]-(self.PgMax))**2-self.M/(self.state[PgState]-(self.PgMin))**2
        T=np.vstack((T1,T2,T3))

        df=df+T
        self.df=df
        self.lastClientUpdate=np.ones(np.size(self.lastClientUpdate)*self.iterNum)
        return df
    
    def deltaBarrier(self,dstate):
        delta=np.zeros((np.size(dstate)+1,1));
        #code.interact(local=locals())
        if self.refBus==1:
            delta=np.vstack(([0],dstate))
        elif self.refBus==(np.size(dstate)+1):
            delta=np.vstack((dstate,[0]))
        else:
            for i in range(0,self.refBus.astype(int)-1):
                delta[i]=dstate[i]
            delta[self.refBus.astype(int)]=0;
            for i in range(self.refBus,np.size(dstate)+1):
                delta[i]=dstate[i-1];

        db=np.zeros((np.size(delta),1))

        Dt=(self.D)
        Bt=(self.B)
        Pt=(self.P)

        for n in range(0,self.Nt):
            i=(Dt[n,0]-1).astype(int)
            j=(Dt[n,1]-1).astype(int)
            db[i]=db[i]+self.M*Bt[i,j]*(1/(Bt[i,j]*(delta[i]-delta[j])-Pt[i,j])**2-1/(Bt[i,j]*(delta[i]-delta[j])+Pt[i,j])**2)
            db[j]=db[j]+self.M*Bt[j,i]*(1/(Bt[j,i]*(delta[j]-delta[i])-Pt[j,i])**2-1/(Bt[j,i]*(delta[j]-delta[i])+Pt[j,i])**2)
        
        self.db=np.delete(db,self.refBus-1)
        return self.db
    
    def UpdateState(self,df):
        deltaState = np.arange(0,self.Nde).astype(int)
        PdcState = np.arange(self.Nde,self.Nde+self.Ndc).astype(int)
        PdtState = np.arange(self.Nde+self.Ndc,self.Nde+self.Ndc+self.Ndt).astype(int)
        PgState = np.arange(self.Nde+self.Ndc+self.Ndt,self.Nde+self.Ndc+self.Ndt+self.Ng).astype(int)
        lambdaState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr).astype(int)
        lambdahatState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr).astype(int)
        PdkState = np.arange(self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr,self.Nde+self.Ndc+self.Ndt+self.Ng+self.Nr+self.Nr+self.Ndk).astype(int)
        
        if df is None:
            df=self.df
        

        
        db=self.deltaBarrier(self.state[deltaState])
        db=np.expand_dims(db,1)
        dfn=np.vstack((db,df))

        #Pdkt=np.expand_dims((Pdk[k]),1)
        #code.interact(local=locals())
        h=np.dot((self.BnmSumR),self.state[deltaState])+np.dot((self.Adc),self.state[PdcState])+np.dot((self.Adt),self.state[PdtState])+np.dot((self.Adk),self.Pdk)-np.dot((self.Ag),self.state[PgState])

        
        self.state[lambdahatState]=np.dot(self.m1,(h-np.dot(self.m2,dfn)))

        G=dfn+np.dot(self.N,self.state[lambdahatState])

        tmp=self.alpha*np.dot(self.Hhatinv,G)
        tidx=np.arange(0,self.Nde+self.Ndc+self.Ndt+self.Ng).astype(int)
        self.state[tidx]=self.state[tidx]-tmp[tidx]

        tmp=self.alpha*self.c*h
        self.state[lambdaState]=self.state[lambdahatState]-tmp
        
        self.iterNum+=1
        #if self.iterNum >= 42:
        #   code.interact(local=locals())
        
    def getClientDispatch(self,clientName):
        PdcState = np.arange(self.Nde,self.Nde+self.Ndc).astype(int)
        PdtState = np.arange(self.Nde+self.Ndc,self.Nde+self.Ndc+self.Ndt).astype(int)
        PgState = np.arange(self.Nde+self.Ndc+self.Ndt,self.Nde+self.Ndc+self.Ndt+self.Ng).astype(int)
        
        inData=clientName.split('-')
        type=inData[0]
        idx=int(inData[1])
        
        if type == 'DC':
            dispatch=self.state[PdcState[idx]]
        elif type == 'DT':
            dispatch=self.state[PdtState[idx]]
        elif type == 'G':
            dispatch=self.state[PgState[idx]]
        else:
            dispatch=-99999
        
        return dispatch[0]
    
    def setClientUtil(self,clientName,utilVal):
        PdcUtil = np.arange(0,self.Ndc).astype(int)
        PdtUtil = np.arange(self.Ndc,self.Ndc+self.Ndt).astype(int)
        PgUtil = np.arange(self.Ndc+self.Ndt,self.Ndc+self.Ndt+self.Ng).astype(int)
        
        inData=clientName.split('-')
        type=inData[0]
        idx=int(inData[1])
        
        if type == 'DC':
            self.df[PdcUtil[idx]]=utilVal
            self.lastClientUpdate[PdcUtil[idx]]=self.iterNum
        elif type == 'DT':
            self.df[PdtUtil[idx]]=utilVal
            self.lastClientUpdate[PdtUtil[idx]]=self.iterNum
        elif type == 'G':
            self.df[PgUtil[idx]]=utilVal
            self.lastClientUpdate[PgUtil[idx]]=self.iterNum
        
    
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
        
        fstr=path + '/fullcase.json'
        f=open(fstr,'w')
        f.write(json.dumps(jsonVals))
        f.flush()
        f.close()
        
        #determine client-node assignments
        numNodes=1
        jsonVals=defaultdict(lambda: defaultdict(list))
        
        for i in range(0,numNodes):
            nodeName='nodeIsoClient-' + str(i+1)
            numDc=self.Ndc
            numDt=self.Ndt
            numG=self.Ng
            idx=0;
            for k in range(0,numDc):
                jsonVals[nodeName][str(idx)]='DC,'+str(k)
                idx += 1
            for k in range(0,numDt):
                jsonVals[nodeName][str(idx)]='DT,'+str(k)
                idx += 1
            for k in range(0,numG):
                jsonVals[nodeName][str(idx)]='G,'+str(k)
                idx += 1
        
        fstr=path + '/clientAssignment.json'
        f=open(fstr,'w')
        f.write(json.dumps(jsonVals))
        f.flush()
        f.close()
        
        
        cl=self.getClientList()
        fstr=path+'/clist.txt'
        f=open(fstr,'w')
        f.write(json.dumps(cl))
        f.flush()
        f.close()
        
        #Create the AAL file
        
    
    def getStateData(self):
        statelist=self.state.tolist()
        return statelist
    
    def getClientList(self):
        clientList={}
        k=0
        for i in range(0,self.Ndc):
            clientList['DC-'+str(i)]=k
            k+=1
        for i in range(0,self.Ndt):
            clientList['DT-'+str(i)]=k
            k+=1
        for i in range(0,self.Ng):
            clientList['G-'+str(i)]=k
            k+=1
        return clientList

    def __init__(self, path, caseNum,c,gamma,M,k,alpha):
        self.caseNum=caseNum
        self.c=c
        self.gamma=gamma
        self.M=M
        self.k=k
        self.alpha=alpha
        self.loadCase(path)
        