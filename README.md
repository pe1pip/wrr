# WRR - something

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

or whatever these packages are called on your favourite OS/Distro

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


