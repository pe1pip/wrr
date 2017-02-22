from flask import Flask, Response
from redis import StrictRedis
from time import sleep

app = Flask(__name__)
redis = StrictRedis()

def eventStream():
	pubsub = redis.pubsub(ignore_subscribe_messages=True)
	pubsub.subscribe('trx1')
	try:
		for message in pubsub.listen():
			freq = message['data']
			freq = int(freq.decode('ascii'))
			tfreq = freq + 1886000000
			print(tfreq)
			sh = freq % 1000
			sk = (freq // 1000) % 1000
			sm = ( freq // 1000000 ) % 1000
			sg = ( freq // 1000000000 ) % 1000
			mh = tfreq % 1000
			mk = (tfreq // 1000) % 1000
			mm = ( tfreq // 1000000 ) % 1000
			mg = ( tfreq // 1000000000 ) % 1000
			print("{} {} {} {}".format(mg, mm, mk, mh))
			md = '"mg": "{:02d}", "mm": "{:03d}", "mk": "{:03d}", "mh": "{:03d}"'.format(mg, mm, mk, mh)
			sd = '"sg": "{:02d}", "sm": "{:03d}", "sk": "{:03d}", "sh": "{:03d}"'.format(sg, sm, sk, sh)
			print("{{ {}, {} }}".format(md, sd))
			yield "data: {{ {}, {} }}\n\n".format(md, sd)
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
