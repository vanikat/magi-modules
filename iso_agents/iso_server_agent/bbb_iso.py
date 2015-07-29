import code
import random
import time

from local_unit import LocalUnit
from bucket import Bucket
from battery import Battery
from bakery import Bakery

# degug notes:
#code.interact(local=dict(globals(), **locals())) 
# import pdb
#pdb.set_trace()

class BBB_ISO(object):

    def __init__(self):
        self.unitList={}
        self.tS=1.0
        self.UID=0 #unique ID for assigning to clients
        self.currentTime=0
    
    def agileBalancing(self, k, pDispatch):
        self.currentTime = k
        initialPDispatch = pDispatch
        unitGroups= {
            'Bucket': [],
            'Battery': [],
            'Bakery': []
        }
        for key,val in self.unitList.iteritems():
            val.updateE(k)
            val.updateAgility(k)
            val.updatePForced()
            unitType = val.__class__.__name__
            # if unitType not in unitGroups:
            #   unitGroups[unitType]=[]
            unitGroups[unitType].append(val)

        pBatteriesForced = 0.0
        for unit in unitGroups['Battery']:
            pBatteriesForced += unit.pForced
        
        pBakeriesForced = 0.0
        for unit in unitGroups['Bakery']:
            pBakeriesForced += unit.pForced
        
        pForced = pBatteriesForced + pBakeriesForced
        
        pBucketsAvailable = 0.0
        for unit in unitGroups['Bucket']:
            pBucketsAvailable += unit.pAvailable()

        # pBucketsAvailable = reduce(
        #   lambda x,y:x+y, [b.pAvailable() for b in unitGroups['Bucket']]
        # )
        totalPAvailable = pDispatch + pBucketsAvailable
        if pForced > pDispatch:
            # Just give all batts & bakes the power we're forced to
            # Draw on power from buckets if necessary
            for unit in (unitGroups['Battery'] + unitGroups['Bakery']):
                p = min(unit.pForced, totalPAvailable)
                unit.setP(p)
                totalPAvailable = totalPAvailable - p
        else:
            # Sort Batteries and Bakeries according to increasing agility factor.
            # Distribute PDispatch to Batteries and Bakeries in increasing agility factor order and such that PBatteries(k) + PBakeries(k) is as large as possible, but less than or equal to PDispatch(k).
            bakeriesAndBatteries = sorted(
                unitGroups['Battery'] + unitGroups['Bakery'], 
                key=lambda b: b.agility
            )
            for b in bakeriesAndBatteries:
                p = min(b.pMax, (b.eMax - b.e)/self.tS, pDispatch)
                b.setP(p)
                pDispatch = pDispatch - p

        # pBatteries = reduce(
        #   lambda x,y: x+y, [b.p for b in unitGroups['Battery']]
        # )
        # pBakeries = reduce(
        #   lambda x,y: x+y, [b.p for b in unitGroups['Bakery']]
        # )
        pBatteries = 0.0
        for unit in unitGroups['Battery']:
            pBatteriesForced += unit.p
        
        pBakeries = 0.0
        for unit in unitGroups['Bakery']:
            pBakeriesForced += unit.p
        
        pDispatch = initialPDispatch - pBatteries - pBakeries

        # Distribute remaining pDispatch to the Buckets in decreasing agility factor order.
        unitGroups['Bucket'].sort(key=lambda b: b.agility,reverse=True)
        for b in unitGroups['Bucket']:
            if pDispatch < 0:
                # must draw on buckets' power
                p = max(-b.pAvailable(), pDispatch) 
            else:
                # send power to buckets for future use
                p = min(b.pReserve(), pDispatch)
            b.setP(p)
            pDispatch = pDispatch - p

    def start(self):
        pass

    def registerClient(self, CID, clientParams):
        UID = self.UID
        self.UID += 1
        newUnit = BBB_ISO.dictToUnit(clientParams)
        newUnit.UID = UID
        self.unitList[CID] = newUnit

    def deregisterClient(self, CID):
        if CID in self.unitList:
            del self.unitList[CID]

    def setParam(self, CID, params):
        if CID in self.unitList:
            cl=self.unitList[CID]
            cl.rehashParams(params)

    def getReply(self, CID):
        data = {}
        if CID in self.unitList:
            data['p'] = self.unitList[CID].p
            data['currentTime'] = self.currentTime
        else:
            data["p"] = 123456789
            data["currentTime"] = 123456789
            raise Exception, "CID unknown! Unit not in unitList!"
        return data

    def generateStats(self,t,lastDispatch):
        units = self.unitList
        unitGroups={
            'Bucket': [],
            'Battery': [],
            'Bakery': []
        }
        for key,val in self.unitList.iteritems():
            unitType = val.__class__.__name__
            if unitType not in unitGroups:
                unitGroups[unitType]=[]
            unitGroups[unitType].append(val)
        battP = 0
        buckP = 0
        bakeP = 0
        for val in unitGroups['Battery']:
            battP = battP + val.p
        for val in unitGroups['Bucket']:
            buckP = buckP + val.p
        for val in unitGroups['Bakery']:
            bakeP = bakeP + val.p
        
        pResidual = lastDispatch-battP-buckP-bakeP

        data = {}
        data["t"] = t
        data["pDispatch"] = lastDispatch
        data["pResidual"] = pResidual
        data["bucketP"] = buckP
        data["batteryP"] = battP
        data["bakeryP"] = bakeP
        data["units"] = {}

        for k,v in units.iteritems():
            data["units"]["k"] = v.__dict__

        return data
        

    @staticmethod
    def dictToUnit(client):
        cmd='newUnit=BBB_ISO.dictTo'+client["type"]+'(client)'
        exec(cmd)
        newUnit.type=client["type"]
        return newUnit
    
    @staticmethod
    def dictToBakery(client):
        eMin=client["eMin"]
        eMax=client["eMax"]
        pMin=client["pMin"]
        pMax=client["pMax"]
        tEnd=client["tEnd"]
        e=client["e"]
        p=client["p"]
        tRun=client["tRun"]
        CID=client["CID"]
        return Bakery(eMin, eMax, pMin, pMax, tEnd, tRun, e, p)
    
    @staticmethod
    def dictToBattery(client):
        eMin=client["eMin"]
        eMax=client["eMax"]
        pMin=client["pMin"]
        pMax=client["pMax"]
        tEnd=client["tEnd"]
        e=client["e"]
        p=client["p"]
        CID=client["CID"]
        return Battery(eMin, eMax, pMin, pMax, tEnd, e, p)
    
    @staticmethod
    def dictToBucket(client):
        eMin=client["eMin"]
        eMax=client["eMax"]
        pMin=client["pMin"]
        pMax=client["pMax"]
        e=client["e"]
        p=client["p"]
        CID=client["CID"]
        return Bucket(eMin, eMax, pMin, pMax, e, p)



