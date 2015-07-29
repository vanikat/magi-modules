from local_unit import LocalUnit

class Bakery(LocalUnit):

	def __init__(self, eMin, eMax, pMin, pMax, tEnd, tRun, e, p):
		super(Bakery, self).__init__(e, eMin, eMax, p, pMin, pMax)
		self.tEnd = tEnd
		self.tRun = tRun
		self.v = 0
		self.updateAgility(0)
		self.updatePForced()

	def updateE(self,k):
		self.e += (self.p*self.tS)
		if self.e == self.eMax:
			self.v = 0
		return self.e

	def setP(self, newP):
		self.p = newP
		if (self.p > 0):
			self.v = True
		return self.p

	def updateAgility(self,k):
		if self.v:
			self.agility = 0
		else:
			self.agility = self.tEnd - self.tRun - k
		return self.agility

	def updatePForced(self):
		if self.agility <= 0 and self.e < self.eMax:
			self.pForced = self.pMax
		else:
			self.pForced = 0.0
		return self.pForced

if __name__=="__main__":
	# write new tests....
	pass