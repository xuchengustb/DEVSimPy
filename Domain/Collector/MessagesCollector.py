# -*- coding: utf-8 -*-

"""
Name : MessagesCollector.py 
Brief descritpion : collect to disk received messages 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 7/10/11
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5


import os
import random

from DomainInterface.DomainBehavior import DomainBehavior

#  ================================================================    #
class MessagesCollector(DomainBehavior):
	"""	Messages Collector
	"""

	###
	def __init__(self, fileName = os.path.join(os.getcwd(),"result%d"%random.randint(1,100)), ext = '.dat', comma = ""):
		""" Constructor.
		
			@param fileName : name of output fileName
			@param ext : output file extension
			@param comma : comma separated
		"""
		DomainBehavior.__init__(self)
		
		# local copy
		self.fileName = fileName
		self.ext = ext
		self.comma = comma
	
		self.initPhase('IDLE',INFINITY)

		for np in range(10000):
			fn = "%s%d%s"%(self.fileName, np, self.ext)
			if os.path.exists(fn):
				os.remove(fn)
	###
	def extTransition(self, *args):
		"""
		"""
		
		for port in self.IPorts:
			### adapted with PyPDEVS
			msg = self.peek(port, *args)
			
			if msg:
				np = self.getPortId(port)
			
				### filename
				fn = "%s%s%s"%(self.fileName, str(np), self.ext)
				
				with open(fn,'a') as f: f.write("%s\n"%(str(msg)))
				del msg

		self.holdIn('ACTIF',0)

		return self.getState()
		
	###
	def intTransition(self):
		self.passivateIn('IDLE')
		return self.getState()
		
	###
	def timeAdvance(self):return self.getSigma()
	
	###
	def __str__(self):return "MessagesCollector"