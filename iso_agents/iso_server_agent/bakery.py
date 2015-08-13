from local_unit import LocalUnit

class Bakery(LocalUnit):

	def __init__(self, eMin, eMax, pMin, pMax, tEnd, tRun, e, p):
		super(Bakery, self).__init__(e, eMin, eMax, p, pMin, pMax)
		self.tEnd = tEnd
		self.tRun = tRun
		self.v = False
		self.updateAgility(0)
		self.updatePForced()

	def setP(self, newP):
		self.p = newP
		if (self.p > 0):
			self.v = True

	def updateAgility(self, k):	
		self.agility = self.tEnd - self.tRun - k

	def updatePForced(self):
		if self.agility > 1 and self.v is False:
			self.pForced = 0.0
		else:
			self.pForced = self.getConstrainedPMax()

if __name__=="__main__":
	# write new tests....
	pass






