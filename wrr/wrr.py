from flask import Flask, Response
from redis import StrictRedis
from time import sleep

app = Flask(__name__)
redis = StrictRedis()

def mkfreq():
	freq = int()
    vfo = redis.hget('trx1','vfo')
    print("vfo: {}".format(vfo))
    vfo = vfo.decode('ascii')
    frq = redis.hget('trx1','{}_freq'.format(vfo))
    freq = int(frq.decode('ascii'))
    tfreq = freq + 1886000000
    sh = freq % 1000
    sk = (freq // 1000) % 1000
    sm = ( freq // 1000000 ) 
    mh = tfreq % 1000
    mk = (tfreq // 1000) % 1000
    mm = ( tfreq // 1000000 )
    print("{} {} {}".format(mm, mk, mh))
    md = '"mm": "{:04d}", "mk": "{:03d}", "mh": "{:03d}"'.format(mm, mk, mh)
    sd = '"sm": "{:04d}", "sk": "{:03d}", "sh": "{:03d}"'.format(sm, sk, sh)
    print("{{ {}, {} }}".format(md, sd))
    return 'data: {{ "freq": {{ {}, {} }} }}\n\n'.format(md, sd)

def mkrxled():
    tx = int(redis.hget('trx1','ptt'))
    rx = int(redis.hget('trx1','squelsh'))
	led = 'off'
	if tx:
		led = 'tx'
	else:
		if rx:
			led = 'rx'
	return 'data: {{ "led": "{}" }}'.format(led)

def eventStream():
	pubsub = redis.pubsub(ignore_subscribe_messages=True)
	pubsub.subscribe('trx1')
	try:
		for message in pubsub.listen():
			mtype = message['data']
			mtype = mtype.decode('ascii')
			if mtype == 'freq':
				data = mkfreq()
				continue
			if mtype == 'ps':
				data = mkrxled()
			if mtype == 'tx':
				continue
			if mtype == 'rx':
				continue
			if mtype == 'dummy':
				data = 'data: { "dummy": "0" }\n\n'
            yield data

	except GeneratorExit:
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
