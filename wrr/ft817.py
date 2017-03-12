#!/usr/bin/python3

from redis import StrictRedis
import serial

redis = StrictRedis()

# redis structure
# pubsub trx1 possible messages:
#  - freq: vfo, mode and/or frequency changed
#  - ps: ptt or squelsh open indication changed
#  - tx: split, hiswr or pmeter changed
#  - rx: discr, code or smeter changed

# trx1 data structure
# - a_freq: frequency on vfo a
# - a_mode: mode on vfo a
# - b_freq: frequency on vfo b
# - b_mode: mode on vfo b
# - vfo: a or b
# - ptt: True if the PTT is not active
# - squelch: is the squelsh active (=not open)?
# - smeter: value (0-15) on the s meter
# - pmeter: value (0-15) of the power meter
# - discr: is the FM discriminator locked
# - code: is the CTCSS code matched (or off)
# - split: are we in split TX operation?
# - hiswr: is the SWR too high?

modes = {
	0: "lsb",
	1: "usb",
	2: "cw",
	3: "cwr",
	4: "am",
	6: "wfm",
	8: "fm",
	10: "dig",
	12: "pkt"
}

commands = {
	'read_rx' : '00 00 00 00 e7',
	'read_tx' : '00 00 00 00 f7',
	'read_freq' : '00 00 00 00 03',
	'lock_on' : '00 00 00 00 00',
	'lock_off' : '00 00 00 00 80',
	'ptt_on' : '00 00 00 00 08',
	'ptt_off' : '00 00 00 00 88',
	'set_freq' : '00 00 00 00 01',
	'set_mode' : '00 00 00 00 07',
	'clar_on' : '00 00 00 00 05',
	'clar_off' : '00 00 00 00 85',
	'set_clar' : '00 00 00 00 f5',
	'toggle_vfo' : '00 00 00 00 81',
	'split_on' : '00 00 00 00 02',
	'split_off' : '00 00 00 00 82',
	'dup_up' : '49 00 00 00 09',
	'dup_down' : '09 00 00 00 09',
	'dup_off' : '89 00 00 00 09',
	'set_dup' : '00 00 00 00 f9',
	'tone_dcs' : '0a 00 00 00 0a',
	'tone_ctcss' : '2a 00 00 00 0a',
	'tone_enc' : '4a 00 00 00 0a',
	'tone_off' : '8a 00 00 00 0a',
	'set_tone' : '00 00 00 00 0b',
	'set_dcs' : '00 00 00 00 0c',
	'power_on' : '00 00 00 00 0f',
	'power_off' : '00 00 00 00 8f'
	}

class vfo:
	def __init__(self):
		self.freq = int()
		self.mode = ""

class trx:
	def __init__(self, pubsubname="trx1", serialname="/dev/ttyS0"):
		self.vfoa = vfo()	# ft-817 has 2 VFO's
		self.vfob = vfo()
		self.vfo = "a"		# no way of knowing which one is active, so we assume a
		self.smeter = int()
		self.discr = bool()
		self.code = bool()
		self.squelsh = bool()
		self.pmeter = int()
		self.split = bool()
		self.hiswr = bool()
		self.ptt = bool()
		self.pubsub = pubsubname
		self.serialname = serialname
		self.serialport = serial.Serial(serialname, 4800, timeout=0.2)

	def printFreq(self):
		print(self.vfoa.freq)

	def printMode(self):
		print(self.vfoa.mode)

	def pubDummy(self):
		redis.publish(self.pubsub,"dummy")

	def readRX(self):
		cmd = bytes.fromhex('00 00 00 00 e7')
		self.serialport.write(cmd)
		rxstat = self.serialport.read(1)
		rxstat = list(rxstat)[0]
		sq = rxstat & 128
		sq = bool(sq)
		code = rxstat & 64
		code = bool(code)
		discr = rxstat & 32
		discr = bool(discr)
		s = int(rxstat & 15)
		up_ps=False
		up_rx=False
		if s != self.smeter:
			self.smeter = s
			redis.hset(self.pubsub,"smeter",s)
			up_rx=True
			
		if sq != self.squelsh:
			self.squelsh = sq
			redis.hset(self.pubsub,"squelsh",sq)
			up_ps = True

		if code != self.code:
			self.code = code
			redis.hset(self.pubsub,"code",code)
			up_rx = True

		if discr != self.discr:
			self.discr = discr
			redis.hset(self.pubsub,"discr",discr)
			up_rx = True
		# publish the updates
		if up_rx:
			redis.publish(self.pubsub,"rx")
		if up_ps:
			redis.publish(self.pubsub,"ps")

	def readTX(self):
		cmd = bytes.fromhex('00 00 00 00 f7')
		self.serialport.write(cmd)
		txstat = self.serialport.read(1)
		txstat = list(txstat)[0]
		ptt = txstat & 128
		ptt = not bool(ptt)
		hiswr = txstat & 64
		hiswr = bool(hiswr)
		split = txstat & 32
		split = bool(split)
		pmeter = txstat & 15
		up_ps = False
		up_tx = False
		#
		if ptt != self.ptt:
			self.ptt = ptt
			redis.hset(self.pubsub,"ptt",ptt)
			up_ps = True
		if ptt:	# values are only valid if PTT is active
			#
			if pmeter != self.pmeter:
				self.pmeter = pmeter
				redis.hset(self.pubsub,"pmeter",pmeter)
				up_tx = True
			#
			if hiswr != self.hiswr:
				self.hiswr = hiswr
				redis.hset(self.pubsub,"hiswr",hiswr)
				up_tx = True
			#
			if split != self.split:
				self.split = split
				redis.hset(self.pubsub,"split",split)
				up_tx = True
		# publish the updates
		if up_tx:
			redis.publish(self.pubsub,"tx")
		if up_ps:
			redis.publish(self.pubsub,"ps")


	def readFreqMode(self):
		# send the command to the rig
		cmd = bytes.fromhex('00 00 00 00 03')
		self.serialport.write(cmd)
		# read the reply
		freqmode = self.serialport.read(5)
		freqmode = list(freqmode)
		# determine the vfo
		vfo = self.vfoa
		if self.vfo == 'b':
			vfo = self.vfob
		# do not send an update unless something changed
		up_freq = False
		# first 4 bytes are the frequency in packed bcd in 10 Hz 
		freq = 0
		for byte in freqmode[0:4]:
			lsb = byte & 15
			msb = byte >> 4
			freq = ( freq * 100 ) + ( msb * 10 ) + lsb
		freq = freq * 10
		# if the freq changed, update our status, the redis hash and send an update
		if vfo.freq != freq:
			vfo.freq = freq
			redis.hset(self.pubsub,"{}_freq".format(self.vfo),freq)
			up_freq = True
		redis.hset(self.pubsub,"vfo",self.vfo)
		# the mode is in the 5th byte received
		mode = freqmode[4] & 15
		# translate using our dictionary
		if mode in modes:
			mode = modes[mode]
		else:
			print("Guessing mode")
			mode ='ssb'
		# if the mode changed, update our status, the redis hash and send an update
		if vfo.mode != mode:
			vfo.mode = mode
			redis.hset(self.pubsub,"{}_mode".format(self.vfo),mode)
			up_freq = True
		# send the update
		if up_freq:
			redis.publish(self.pubsub,"freq")

	def powerON(self):
		cmd = bytes.fromhex(commands['lock_off'])
		self.serialport.write(cmd)
		cmd = bytes.fromhex(commands['power_on'])
		self.serialport.write(cmd)

	def powerOFF(self):
		cmd = bytes.fromhex(commands['power_off'])
		self.serialport.write(cmd)
