import numpy as np
import scipy as sp
import scipy.io as spio
import scipy.linalg
import h5py
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

class DMM_ISO(object):

    def __init__(self, path):
        self.loadCase(path)
    
    def loadCase(self, path):

        # todo: remove
        self.caseNum = 30
        self.c = 1
        self.gamma = 0.1
        self.M = 0.1
        self.k = 2
        self.alpha = 0.001
        ###

        fName = path + '/case' + str(self.caseNum) + '.mat'
        inData=h5py.File(fName,'r')
        for name in inData:
            cmd='self.' + name + '=np.transpose(np.array(inData.get(\''+name+'\')))'
            exec(cmd)
        
        state = np.vstack((np.zeros((self.Nde,1)),np.ones((self.Ndc,1)) ,  np.ones((self.Ndt,1)),  np.ones((self.Ng,1)),  np.zeros((self.Nr,1)),  np.zeros((self.Nr,1))))
        
        self.state=state
        
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
    
    def setClientUtil(self, clientName, utilVal):
        PdcUtil = np.arange(0,self.Ndc).astype(int)
        PdtUtil = np.arange(self.Ndc,self.Ndc+self.Ndt).astype(int)
        PgUtil = np.arange(self.Ndc+self.Ndt,self.Ndc+self.Ndt+self.Ng).astype(int)
        
        inData = clientName.split('-')
        _type = inData[0]
        idx = int(inData[1])
        
        if _type == 'DC':
            self.df[PdcUtil[idx]]=utilVal
            self.lastClientUpdate[PdcUtil[idx]]=self.iterNum
        elif _type == 'DT':
            self.df[PdtUtil[idx]]=utilVal
            self.lastClientUpdate[PdtUtil[idx]]=self.iterNum
        elif _type == 'G':
            self.df[PgUtil[idx]]=utilVal
            self.lastClientUpdate[PgUtil[idx]]=self.iterNum
        
    def getStateData(self):
        statelist = self.state.tolist()
		#The statelist as a list may be saved as python lists instead of floating values i.e. [1.4412] instead of 1.4412
		#May need to statelist[i][1] index
        return statelist
    
    def getClientList(self):
        clientList = {}
        k = 0
        for i in range(0,self.Ndc):
            clientList['DC-'+str(i)]=k
            k+=1
        for i in range(0,self.Ndt):
            clientList['DT-'+str(i)]=k
            k+=1
        for i in range(0,self.Ng):
            clientList['G-'+str(i)]=k
            k+=1
        return clientL