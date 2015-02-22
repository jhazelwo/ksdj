KSDJ - A Django-based web interface for Kickstart server using NFS & PXE.
=============================================================
**Uses [Python 3.4.2](https://www.python.org/download/releases/3.4.2/) and [Django 1.7.4](https://www.djangoproject.com/download/1.7.4/tarball/)**

### Bugs:
* A typo during client update that is syntactically valid but not logically valid may result in some of the client 
files being removed putting the client in an un-editable state until the files are manually restored from archive.

### TODO:
* Strip out extra '%end' from kickstart config is release is el5.

Deployment notes:
----------------

### VIRTUALENV:
* get the latest from their github repo. v1.9.x doesn't work with py3.4, latest does.

### NGINX 1.7.4:
    ./configure --without-http_rewrite_module --with-http_ssl_module --with-debug && make && make install
    mkdir /usr/local/nginx/ssl/
    cd /usr/local/nginx/ssl/
    openssl genrsa -des3 -out server.key 1024
    openssl req -new -key server.key -out server.csr
    openssl rsa -in server.key.org -out server.key
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

### ksdj_nginx.conf  

```
user apache;
events {
    worker_connections  1024;
}
http {
    upstream django {
        server unix:///tmp/ksdj.socket;
    }
    server {
        listen              443 ssl;
        ssl_protocols       SSLv3 TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        ssl on;
        ssl_certificate /usr/local/nginx/ssl/server.crt;
        ssl_certificate_key /usr/local/nginx/ssl/server.key;
        server_name kickstart.example.tld;
        charset     utf-8;
        location /static/js/ {
            default_type text/javascript;
            alias /opt/www/ksdj/static/js/;
        }
        location /static/css/ {
            default_type text/css;
            alias /opt/www/ksdj/static/css/;
        }  
        location /static/admin/js/ {  
            default_type text/javascript;  
            alias /opt/www/ksdj/static/static/admin/js/;  
        }  
        location /static/admin/css/ {  
            default_type text/css;  
            alias /opt/www/ksdj/static/static/admin/css/;  
        }  
        location / {  
            uwsgi_pass  django;  
            include     /usr/local/nginx/conf/uwsgi_params;  
        }  
    }  
}  
```

#### UWSGI (-lts is fine)
    /opt/www/bin/uwsgi -H/opt/www -s /tmp/ksdj.socket --uid=apache --gid=apache --module ksdj.wsgi --chmod-socket=600 --enable-threads >> /var/log/uwsgi.log 2>&1 &

* Slightly better versions of that stuff is in /etc/init.d/Kickstart and takes args (start|stop|bounceweb)


### DB Migrate
    cd /opt/www/
    source bin/activate
    cd ksdj
    python manage.py makemigrations
    python manage.py migrate
