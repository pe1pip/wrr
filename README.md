# WRR - something

A web-based remote control for your HAM radio RIG, in python, html5 and javascript.

Goals:

 1. display the rig freqency, mode, etc.
 2. display everything
 3. control everything less PTT
 4. 2-way audio streams
 5. control PTT

Note that part of 1. is that I own transverters and this code displays the input/output freq. of the transverter.

So further goals:

 6. Control transverter off-set
 7. Select a transverter

## Screenshot

![alt text](https://github.com/pe1pip/wrr/blob/master/WRR%20-%20Screen%20Shot.png WRR - Screen Shot)

## Note:

Code is in alpha state. I've been able to display the freq. on the rig on the website, but nothing more has been tested.

## Setup:

install:

 * nginx
 * uwsgi
 * uwsgi-python3
 * python3
 * python3-flask
 * python3-redis
 * python3-serial
 * redis-server

or whatever these packages are called on your favourite OS/Distro. Be sure to have something fairly recent. Debian stable won't do, testing will. Most notably you want a recent version of flask (0.12) and redis (3.2.6 or 'better'). Of course nobody forces you to user nginx and uwsgi, but this is what I use and works for me.

I just started woring in /var/www/html and /var/www/wrr, if you like other paths better, feel free to adjust the nginx and uwsgi configs as you see fit. 

## nginx

````
server {
	listen 80 default_server;
	listen [::]:80 default_server;

	root /var/www/html;

	index index.html;

	server_name _;

	location / {
		# First attempt to serve request as file, then
		# as directory, then fall back to displaying a 404.
		try_files $uri $uri/ =404;
	}

	location = /wrr { rewrite ^ /wrr/; }
	location /wrr {
		try_files $uri @wrr;
		# proxy_set_header Connection '';
		# proxy_http_version 1.1;
		# chunked_transfer_encoding off;
		# proxy_buffering off;
		# proxy_cache off;
	}
	location @wrr {
  		include uwsgi_params;
  		uwsgi_pass unix:/tmp/wrr.sock;
	}
}
````

## uwsgi

````
[uwsgi]
uid = www-data
gid = www-data
socket = /tmp/wrr.sock
plugins = python3
mount = /wrr=wrr.py
callable = app
chdir = /var/www/wrr
touch-reload = /var/www/wrr/touch
manage-script-name
````


