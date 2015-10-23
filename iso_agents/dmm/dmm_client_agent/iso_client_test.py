from threading import Thread
from iso_client import iso_client
import json
import sys
import time

class iso_client_test:
	def __init__(self,file,server):
		self.scenarioFile=file
		self.clientList={}
		self.isoServer=server
		self.running=1
		return
		
	def loadClients(self,datafile):
		f=open(datafile,'r')
		jin=f.read()
		data=json.loads(jin)
		for key,val in data.iteritems():
			self.clientList[key]=val
		return
	
	def startClientThread(self,clientID):
		iclt=iso_client()
		iclt.clientID=clientID
		iclt.isoServer=self.isoServer
		iclt.scenarioFile=self.scenarioFile
		iclt.connectISO('')
		while self.running:
			pass
		iclt.cleanup('')
		return
	
	def startClients(self):
		for key,val in self.clientList.iteritems():
			nthread=Thread(name=key,target=self.startClientThread,args=(key,))
			nthread.start()
			time.sleep(0.05)
		return
	
	def stopClients(self):
		self.running=0
		return
