## Server setup (Ubuntu 16.04)

### Basics

```
$ sudo apt-get install git build-essential python3-dev libxml2-dev libxslt-dev
```

### Firewall

Install ufw,
```
$ sudo apt-get instsall ufw
```

Configure,
```
$ sudo ufw allow ssh
$ sudo ufw allow http
$ sudo ufw allow https
$ sudo ufw default deny incoming
$ sudo ufw default allow outgoing
```

Enable,
```
$ sudo ufw enable
```

View status,
```
$ sudo ufw status
```

### Database (PostgreSQL)
Install system dependencies,
```
$ sudo apt-get install libpq-dev postgresql postgresql-contrib
```

Switch to the postgres user,
```
$ sudo su - postgres
```

Start a Postgres session and create a new database and user,
```
$ sudo -su postgres
$ psql
$ CREATE DATABASE openkamer;
$ CREATE USER openkamer WITH PASSWORD 'password';
```

Set a few user settings,
```
$ ALTER ROLE openkamer SET client_encoding TO 'utf8';
$ ALTER ROLE openkamer SET timezone TO 'UTC';
```

Give the new user access rights and exit the Postgres session,
```
$ GRANT ALL PRIVILEGES ON DATABASE openkamer TO openkamer;
$ \q
```

Set the database user and password in `local_settings.py`.

### Web server
The web server is a combination of nginx, uWSGI and Django.

The setup is largely based on these instructions: http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html.  
These instructions are tested on an Ubuntu 16.04 VPS.

#### nginx
The nginx conf file is located in `/etc/nginx/sites-enabled/`, an example is found in the `docs/config` directory of the project.

Install nginx,
```
$ sudo apt-get install nginx
```
Copy the nginx config in `docs/config/` to `/etc/nginx/sites-enabled/` and set the correct project paths in the config file.

The config assumes you are deploying with HTTPS. 
Create certificates with 'Let's Encrypt', then create a `/etc/nginx/snippets/ssl-openkamer.org.conf` with the following content,
```
ssl_certificate /etc/letsencrypt/live/openkamer.org/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/openkamer.org/privkey.pem;
```

Restart nginx,
```
$ sudo service nginx restart
```

#### uWSGI
Install uWSGI,
```
$ source env/bin/activate
$ pip install uwsgi
```

Create a systemd startup config,
```
$ sudo cp docs/config/uwsgi.service /etc/systemd/system/uwsgi_openkamer.service
```

Create uwsgi log directory if it does not exist,
```
$ sudo mkdir /var/log/uwsgi
```

Start the uwsgi service and check its status,
```
$ sudo systemctl start uwsgi_openkamer
$ sudo systemctl status uwsgi_openkamer
```
In case of problems, start the uwsgi command `ExecStart` from `uwsgi_openkamer.service` manually to see what is wrong.

Enable on startup,
```
$ sudo systemctl enable uwsgi_openkamer
```

### Search (Solr)

Install Solr by following these instructions: https://cwiki.apache.org/confluence/display/solr/Taking+Solr+to+Production

```bash
$ sudo systemctl start solr
$ sudo systemctl status solr
```

Create core,
```bash
$ /opt/solr-6.5.1/bin/solr create -c default5
```

Create symbolic links of the config files,
```bash
$ ln -s openkamer/website/templates/search_configuration/solrconfig.xml /var/solr/data/default5/conf/solrconfig.xml
$ ln -s openkamer/website/templates/search_configuration/schema.xml /var/solr/data/default5/conf/schema.xml
$ ln -s openkamer/website/templates/search_configuration/stemdict_nl.txt /var/solr/data/default5/conf/stemdict_nl.txt
```

Reload core,
```bash
$ curl 'http://localhost:8983/solr/admin/cores?action=RELOAD&core=default5&wt=json&indent=true'
```

Create search index,
```
$ python manage.py rebuild_index
```

Enable on startup,

```bash
$ sudo systemctl enable solr
```

Logs can be found in `/var/solr/data/default5/conf/logs`.