from flask import Flask, Response, request, jsonify
from redis import StrictRedis
from time import sleep

app = Flask(__name__)
redis = StrictRedis()
offset = 1886000000

offsets = {
	"None - 0 MHz": 0,
	"23cm - 1154 MHz": 1152000000,
	"13cm - 1886 MHz": 1886000000,
	"13cm - 1888 MHz": 1888000000,
	"9cm - 2966 MHz": 2966000000,
	"9cm - 2968 MHz": 2968000000,
	"6cm - 5326 MHz": 5326000000,
	"6cm - 5328 MHz": 5328000000
}

def setOffset(val):
	if val in offsets:
		offset = offsets[val]
		print("offset set to {}".format(offset))
		redis.hset('trx1','offset',offset)
		redis.publish('trx1','freq')
		return 204
	else:
		return 404

def mkfreq():
	freq = int()
	vfo = redis.hget('trx1','vfo')
	print("vfo: {}".format(vfo))
	vfo = vfo.decode('ascii')
	frq = redis.hget('trx1','{}_freq'.format(vfo))
	mode = redis.hget('trx1','{}_mode'.format(vfo))
	mode = mode.decode('ascii')
	freq = int(frq.decode('ascii'))
	offset = redis.hget('trx1','offset')
	offset = offset.decode('ascii')
	offset = int(offset)
	print("offset is {}".format(offset))
	tfreq = freq + offset
	sh = freq % 1000
	sk = (freq // 1000) % 1000
	sm = ( freq // 1000000 ) 
	mh = tfreq % 1000
	mk = (tfreq // 1000) % 1000
	mm = ( tfreq // 1000000 )
	# print("{} {} {}".format(mm, mk, mh))
	md = '"mm": "{:04d}", "mk": "{:03d}", "mh": "{:03d}"'.format(mm, mk, mh)
	sd = '"sm": "{:04d}", "sk": "{:03d}", "sh": "{:03d}"'.format(sm, sk, sh)
	# print("{{ {}, {} }}".format(md, sd))
	fd = '"freq": {{ {}, {} }}'.format(md, sd)
	md = '"mode": "{}"'.format(mode)
	vd = '"vfo": "{}"'.format(vfo)
	return 'data: {{ {}, {}, {} }}\n\n'.format(fd, md, vd)

def mkrxled():
	tx = int(redis.hget('trx1','ptt'))
	rx = int(redis.hget('trx1','squelsh'))
	led = 'off'
	if tx:
		led = 'tx'
	else:
		if rx:
			led = 'rx'
	return 'data: {{ "led": "{}" }}\n\n'.format(led)

def eventStream():
	pubsub = redis.pubsub(ignore_subscribe_messages=True)
	pubsub.subscribe('trx1')
	try:
		for message in pubsub.listen():
			mtype = message['data']
			mtype = mtype.decode('ascii')
			if mtype == 'freq':
				data = mkfreq()
			if mtype == 'ps':
				data = mkrxled()
			if mtype == 'tx':
				continue
			if mtype == 'rx':
				continue
			if mtype == 'dummy':
				data = 'data: { "dummy": "0" }\n\n'
			print(data)
			yield data

	except GeneratorExit:
		pubsub.unsubscribe('trx1')
	except OSError:
		pubsub.unsubscribe('trx1')
	

@app.route('/')
def route():
	mf = redis.get('main_freq')
	mf = mf.decode("ascii")
	return mf

@app.route('/stream')
def stream():
	resp =  Response(eventStream(), mimetype="text/event-stream")
	resp.headers['X-Accel-Buffering'] = 'no'
	return resp

@app.route('/send', methods=['GET', 'POST'])
def send():
	command = request.headers['wrr-command']
	if command == 'set-offset':
		rc = setOffset(request.headers['set-offset'].strip())
	return "", rc
