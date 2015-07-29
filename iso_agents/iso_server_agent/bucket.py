from local_unit import LocalUnit

class Bucket(LocalUnit):

	def __init__(self, eMin, eMax, pMin, pMax, e, p):
		super(Bucket, self).__init__(e, eMin, eMax, p, pMin, pMax)
		self.updateAgility(0)
		self.updatePForced()

	def updateAgility(self,k):
		self.agility = (self.eMax-self.e)/(self.tS*self.pMax)
		return self.agility

	def updatePForced(self):
		self.pForced = 0.0
		return self.pForced

	def pReserve(self):
		return min(
			self.pMax, 
			(self.eMax-self.e)/self.tS
		)

	def pAvailable(self):
		return min(
			-self.pMin, 
			(self.e-self.eMin)/self.tS
		)

if __name__=="__main__":
	# write new tests....
	pass