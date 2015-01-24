KSDJ - A Django-based web interface for Kickstart server using NFS & PXE.
=============================================================
Running:  python 3.4.2 && django 1.7.4
--------------------------------------


### Bugs:
* el5.5 doesn't know what '%end' is, 5.10 probably does, 6+ certainly does; have to strip it out before .write()
* email addresses of corporate length probably won't fit- same issue everyone else ran into and is why there are so many 
auth extentions for Dj. Writing my own fix, importing someone elses, or going pure LDAP are all about the same about of 
work so I'm going to go for ldap next chance I get. (that is- if I can get the py3 branch to actually compile)
* A typo during client update that is syntactically valid but not logically valid (like making the IP outside the VLAN) 
will result in some of the client files being removed putting the client in an uneditable state until the files are 
manually restored from archive.

### TODO:
* Review all error checking in kickstart.py, there's quite a bit that can be removed such as:
    * If the tftpboot file for a MAC doesn't exist, client_delete shouldn't fail.
* kickstart.py needs some serious linter love.
* Be sure to add all of the 'create new virtualenv and compile these things' to this file during next
        major upgrade
* Put a 'makemigrations,migrate' script on the kickstart server and make sure folks are aware.


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

#### UWSGI
    -lts is fine
    cd /opt/www/
    source bin/activate
    cd ksdj/
    uwsgi -s /tmp/ksdj.socket --uid=apache --gid=apache --module ksdj.wsgi --chmod-socket=600 --enable-threads


* Slightly better verions of that stuff and the custom interfaces is in /etc/init.d/Kickstart and takes args 
(start|stop|bounceweb)

