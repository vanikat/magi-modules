class LocalUnit(object):

	def __init__(self, e, eMin, eMax, p, pMin, pMax):

		# parameters
		self.eMin = eMin
		self.eMax = eMax
		self.pMin = pMin
		self.pMax = pMax
		self.tS = 1.0
		self.pForced = 0
		self.UID = -1
		self.type = ''
		
		#To capture latency events
		self.lastUpdateTime=0
		
		self.CID = ''

		# current values
		self.e = e
		self.p = p

	def updateE(self, k):
		self.e += (self.p * self.tS)
		return self.e

	def updateAgility(self,k):
		raise NotImplementedError

	def updatePForced(self):
		raise NotImplementedError
	
	def setP(self, newP):
		self.p = newP
		return self.p
		
	def rehashParams(self,params):
		for key,val in params.iteritems():
			cmd='self.'+key+'='
			if type(val) is str:
				cmd=cmd+'\''+val+'\''
			else:
				cmd=cmd+str(val)
			exec(cmd)
		pass
	
	def paramsToDict(self):
		pdict={}
		params=vars(self)
		for key,val in params.iteritems():
			pdict[key]=val
		return params

if __name__=="__main__":
	# write new tests....
	pass