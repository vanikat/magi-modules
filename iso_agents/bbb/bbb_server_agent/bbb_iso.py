import code
import random
import time

from local_unit import LocalUnit
from bucket import Bucket
from battery import Battery
from bakery import Bakery

import logging
log = logging.getLogger(__name__)
class BBB_ISO(object):

    def __init__(self, timeStep = 1.0):
        self.unitList = {}
        self.tS = timeStep
        self.UID = 0 # unique ID for assigning to clients
        self.currentTime = 0

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
            unitGroups[unitType].append(val)

        pBatteriesForced = 0.0
        for unit in unitGroups['Battery']:
            pBatteriesForced += unit.pForced
        
        pBakeriesForced = 0.0
        for unit in unitGroups['Bakery']:
            pBakeriesForced += unit.pForced
        
        pForced = pBatteriesForced + pBakeriesForced

        pUsed = 0.0
        if pForced > pDispatch:
            # Just give all batts & bakes the power we're forced to
            # Draw on power from buckets if necessary
            for unit in (unitGroups['Battery'] + unitGroups['Bakery']):
                p = unit.pForced
                unit.setP(p)
                pUsed += p
        else:
            # Distribute PDispatch to Batteries and Bakeries
            # in increasing agility factor order 
            # and such that PBatteries(k) + PBakeries(k) is as large as possible,
            # but less than or equal to PDispatch(k).
            bakeriesAndBatteries = sorted(
                unitGroups['Battery'] + unitGroups['Bakery'], 
                key=lambda b: b.agility
            )
            
            for i,unit in enumerate(bakeriesAndBatteries):

                if isinstance(unit, Bakery):
                    if (pDispatch - pUsed) >= unit.getConstrainedPMax():
                        p = max(unit.pForced, unit.getConstrainedPMax())
                    else:
                        p = 0.0
                elif isinstance(unit, Battery):
                    p = min(unit.getConstrainedPMax(), pDispatch - pUsed)
                else:
                    raise Exception, "Unknown unit type!"

                unit.setP(p)
                pUsed += p

            #     if i == 7 and k==1:
            #         print "Unit Of interest (7):"
            #         print repr(unit.__dict__)
            #     # pDispatch -= p
                
            # if k==1:
            #     print "Agility List for t=%d:\n%s" % (k, repr([b.agility for b in bakeriesAndBatteries]))
            #     print "P List for t=%d:\n%s" % (k, repr([b.p for b in bakeriesAndBatteries]))

        pBatteries = 0.0
        for unit in unitGroups['Battery']:
            pBatteries += unit.p
        
        pBakeries = 0.0
        for unit in unitGroups['Bakery']:
            pBakeries += unit.p
        
        # pDispatch = initialPDispatch - pBatteries - pBakeries
        pDispatch = initialPDispatch - pUsed

        # Distribute remaining pDispatch to the Buckets 
        # in decreasing agility factor order if pDispatch is positive 
        # and increasing agility factor if pDispatch is positive
        if pDispatch < 0:
            unitGroups['Bucket'].sort(key=lambda b: b.agility)
        else:
            unitGroups['Bucket'].sort(key=lambda b: b.agility,reverse=True)
        
        for b in unitGroups['Bucket']:
            if pDispatch < 0:
                # must draw on buckets' power
                p = max(-b.pAvailable(), pDispatch) 
            else:
                # send power to buckets for future use
                p = min(b.pReserve(), pDispatch)
            b.setP(p)
            pDispatch -= p

    def start(self):
        pass

    def registerClient(self, CID, clientParams):
        if CID in self.unitList:
            log.info("DENIED REGISTRATION TO DUPLICATE CID %s" % CID)
            return

        UID = self.UID
        self.UID += 1
        newUnit = BBB_ISO.dictToUnit(clientParams)
        newUnit.CID = CID
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
        data = {}

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
        
        pResidual = lastDispatch - battP - buckP - bakeP
        
        data["t"] = t
        data["pDispatch"] = lastDispatch
        data["pResidual"] = pResidual
        data["bucketP"] = buckP
        data["batteryP"] = battP
        data["bakeryP"] = bakeP
        data["units"] = []
        data["statsType"] = "iso_stats"

        for k,v in units.iteritems():
            unit = v.__dict__.copy()
            unit["CID"] = k
            data["units"].append(unit)

        # sort units by unit number (e.g. Bak-1, Bat-1, Bkt-1, Bak-2, Bkt-2, etc.)
        data["units"].sort(key=lambda u: int(u["CID"].split("-")[1]))

        return data

    def generatePStats(self, t):
        stats = {}
        stats['p'] = []
        stats['cid'] = []
        stats['t'] = t
        stats['statsType'] = "p"

        units = [x.__dict__.copy() for x in self.unitList.values()]

        for unit in sorted(units, key=lambda x: x["p"]):
            stats['p'].append(unit['p'])
            stats['cid'].append(unit['CID'])

        return stats
    
    def generateAgilityStats(self, t):
        units = [v for k,v in self.unitList.iteritems() if v.type == "Bakery" or v.type == "Battery"]

        try:
            units.sort(key=lambda x: x.agility)
        except AttributeError:
            return {"agility": [], "cid": []}
        agList= []
        cidList = []
        for u in units:
            agList.append(u.agility)
            cidList.append(u.CID)
        return {
            "agility": agList, 
            "cid": cidList, 
            "t": t, 
            "statsType": "agility"
        }

    @staticmethod
    def dictToUnit(client):
        cmd = 'newUnit=BBB_ISO.dictTo' + client["type"] + '(client)'
        exec(cmd)
        newUnit.type = client["type"]
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


        
# pBucketsAvailable = 0.0
# for unit in unitGroups['Bucket']:
#     pBucketsAvailable += unit.pAvailable()

# totalPAvailable = pDispatch + pBucketsAvailable
# p = min(unit.pForced, totalPAvailable)
# totalPAvailable -= p