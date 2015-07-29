from local_unit import LocalUnit

class Battery(LocalUnit):

	def __init__(self, eMin, eMax, pMin, pMax, tEnd, e, p):
		super(Battery, self).__init__(e, eMin, eMax, p, pMin, pMax)
		self.tEnd = tEnd
		self.updateAgility(0)
		self.updatePForced()

	#DG: Lets use k instead of currentTime, since the BBB paper uses k and k*timestep will give us currentTime if we need it
	def updateAgility(self,k):
		self.agility = (
			self.tEnd - k - ((self.eMax-self.e) / (self.tS*self.pMax))
		)
		return self.agility

	def updatePForced(self):
		if self.agility > 1:
			self.pForced = 0.0
		elif self.agility > 0:
			self.pForced = self.pMax*(1-self.agility)
		else:
			self.pForced = self.pMax
		return self.pForced

if __name__=="__main__":
	# write new tests....
	pass