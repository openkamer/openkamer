# openkamer
[![Build Status](https://travis-ci.org/openkamer/openkamer.svg?branch=master)](https://travis-ci.org/openkamer/openkamer) [![Coverage Status](https://coveralls.io/repos/github/openkamer/openkamer/badge.svg?branch=master)](https://coveralls.io/github/openkamer/openkamer?branch=master)

This is a work in progress...

A Python 3.3+ and Django 1.9 project.

### Installation (Linux)

Get the code and enter the project directory,
```
$ git clone https://github.com/openkamer/openkamer.git
$ cd openkamer
```

Install in a local environment (creates a Python 3 virtualenv and a sqlite database file),
```
$ ./install.sh
```

Activate the virtualenv,
```
$ source env/bin/activate
```

Create a superuser,
```
$ python manage.py createsuperuser
```

### Create demo data
Creating data can take several minutes and mostly depends on response time of external sources,
```
$ python manage.py create_data
```

### Run a development server
Run the Django dev web server in the virtualenv,
```
$ source env/bin/activate
(env)$ python manage.py runserver
```

openkamers is now available at http://127.0.0.1:8000 and http://127.0.0.1:8000/admin.
