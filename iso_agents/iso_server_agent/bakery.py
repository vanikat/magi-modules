from local_unit import LocalUnit

class Bakery(LocalUnit):

	def __init__(self, eMin, eMax, pMin, pMax, tEnd, tRun, e, p):
		super(Bakery, self).__init__(e, eMin, eMax, p, pMin, pMax)
		self.tEnd = tEnd
		self.tRun = tRun
		self.v = False
		self.updateAgility(0)
		self.updatePForced()

	def updateE(self,k):
		self.e += (self.p * self.tS)
		if self.e >= self.eMax:
			self.v = False
		return self.e

	def setP(self, newP):
		self.p = newP
		if (self.p > 0):
			self.v = True
		return self.p

	def updateAgility(self, k):	

		self.agility = self.tEnd - self.tRun - k
		
		return self.agility

	def updatePForced(self):
		if self.agility > 1:
			self.pForced = 0.0
		else:
			self.pForced = self.pMax
		
		return self.pForced

if __name__=="__main__":
	# write new tests....
	pass






