#!/usr/bin/python3

from redis import StrictRedis
import serial

redis = StrictRedis()
pubsub = redis.pubsub()

class vfo:
	def __init__(self):
		self.freq = int()
		self.mode = ""

class trx:
	def __init__(self, pubsub="trx1", serialname="/dev/ttyS0"):
		self.vfoa = vfo()	# ft-817 has 2 VFO's
		self.vfob = vfo()
		self.vfo = "a"		# no way of knowing which one is active, so we assume a
		self.smeter = int()
		self.discr = bool()
		self.code = bool()
		self.squelsh = bool()
		self.pmeter = int()
		self.split = bool()
		self.swr = bool()
		self.ptt = bool()
		self.pubsub = pubsub
		self.serialname = serialname
		self.serialport = serial.Serial(serialname, 4800, timeout=0.2)
		

	def printFreq(self):
		print(self.vfoa.freq)

	def readRX(self):
		cmd = bytes.fromhex('00 00 00 00 e7')
		self.serialport.write(cmd)
		rxstat = self.serialport.read(1)
		sq = rxstat & 128
		code = rxstat & 64
		discr = rxstat & 32
		s = int(rxstat & 15)

	def readTX(self):
		cmd = bytes.fromhex('00 00 00 00 f7')
		self.serialport.write(cmd)
		txstat = self.serialport.read(1)

	def readFreqMode(self):
		cmd = bytes.fromhex('00 00 00 00 03')
		self.serialport.write(cmd)
		freqmode = self.serialport.read(5)

trx1 = trx()
trx1.vfoa.freq = 434200000
trx1.printFreq()
