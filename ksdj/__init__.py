"""

    KSDJ - Django interface for Kickstart server using NFS & PXE.
    By: nullpass
    Running:  python 3.4.1 && django 1.7

Bugs:
    el5.5 doesn't know what '%end' is, 5.10 probably does, 6+ certainly does; have to strip it out before .write()
    email addresses of corporate length probably won't fit- same issue everyone else ran into and is why there are
        so many auth extentions for Dj. Writing my own fix, importing someone elses, or going pure LDAP are all about
        the same about of work so I'm going to go for ldap next chance I get.
            ...that is- if I can get the py3 branch to actually compile...
    Editing a client will overwrite any customizations done to its kickstart file.

TODO:
    Breaking client.ks out into parts and storing them in the db to make it possible to retain customizations during client_update.

    Put a 'makemigrations,migrate' script on the kickstart server and make sure folks are aware.

-==-

If I get hit by a bus here are the non-prod deployment notes; of course you don't need to worry about any of this in prod.

VIRTUALENV:
    get the latest from their github repo. v1.9.x doesn't work with py3.4, latest does.

NGINX:
    -1.7.4 works ok
    ./configure --without-http_rewrite_module --with-http_ssl_module --with-debug && make && make install
    mkdir /usr/local/nginx/ssl/
    cd /usr/local/nginx/ssl/
    openssl genrsa -des3 -out server.key 1024
    openssl req -new -key server.key -out server.csr
    openssl rsa -in server.key.org -out server.key
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt


# ksdj_nginx.conf
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

UWSGI
    -lts is fine
    cd /opt/www/
    source bin/activate
    cd ksdj/
    uwsgi -s /tmp/ksdj.socket --uid=apache --gid=apache --module ksdj.wsgi --chmod-socket=600 --enable-threads

Slightly better verions of that stuff and the custom interfaces is in /etc/init.d/Kickstart and takes args (start|stop|bounceweb)


"""
