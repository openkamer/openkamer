## Server setup

### Basics

```
$ sudo apt-get install git build-essential python3-dev
```

### Firewall

Install ufw,
```
$ sudo apt-get instsall ufw
```

Configure,
```
$ sudo ufw allow ssh
$ sudo ufw allow www
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
