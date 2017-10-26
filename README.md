# openkamer
[![Build Status](https://travis-ci.org/openkamer/openkamer.svg?branch=master)](https://travis-ci.org/openkamer/openkamer) [![Coverage Status](https://coveralls.io/repos/github/openkamer/openkamer/badge.svg?branch=master)](https://coveralls.io/github/openkamer/openkamer?branch=master) [![Dependency Status](https://gemnasium.com/badges/github.com/openkamer/openkamer.svg)](https://gemnasium.com/github.com/openkamer/openkamer)

Openkamer gives insight into the Dutch parliament by gathering, organizing and visualizing parliamentary data.

Openkamer gathers (scrapes) parliamentary data from several external sources, creates relations, and visualizes this data in a web application.

Openkamer is a Python 3.4+ and Django 1.10+ project under MIT license. 


## Installation (Linux)

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

### Data
There are 3 options to fill your database with data.

#### Option 1: Load a json dump from openkamer.org (5 min)
This will fill your database with all openkamer data.
Download the latest `openkamer-<date>.json.gz` file from https://www.openkamer.org/database/dumps/.  
Load this data into your local database with the following Django command,
```
$ python manage.py loaddata openkamer-<date>.json.gz
```

#### Option 2: Scrape a small demo data set (10-15 min)
Scrape a demo data subset from external sources. This is the longer, but more exciting method.
Scraping demo data can take several minutes and mostly depends on response time of external sources,
```
$ python manage.py create_demo_data
```

#### Option 3: Scrape all data from scratch (12-24 hours)
This is how you get all data from scratch; scrape everything from external sources.
This will take several hours, but is independent of openkamer.org.  
Use the following command,
```
$ python manage.py create_data
```

### Run a development server
Run the Django dev web server in the virtualenv,
```
$ source env/bin/activate
(env)$ python manage.py runserver
```

Openkamer is now available at http://127.0.0.1:8000 and http://127.0.0.1:8000/admin.

### Configuration

See `website/local_settings.py` and `website/settings.py` for settings.

### Search
based on https://github.com/dekanayake/haystack_solr6
download and install solr-6.5.0 from http://lucene.apache.org/solr/
start and create core
```
$ bin/solr start
$ bin/solr create -c default5
```
You should now be able to visit the admin page at http://127.0.0.1:8983/solr
from website/templates/search_configuration copy solrconfig.xml to [SOLR base folder]server/solr/default5/conf

create schema.xml and refresh core:
```
$ python manage.py build_solr_schema --filename=[SOLR base folder]/server/solr/default5/conf/schema.xml && curl 'http://localhost:8983/solr/admin/cores?action=RELOAD&core=default5&wt=json&indent=true'
```
create search index
```
$ python manage.py rebuild_index
```


## Development

### Testing

##### Run tests
Run all tests,
```
$ python manage.py test
```

Run specific tests (example),
```
$ python manage.py test website.test.TestCreateParliament
```

##### Create test json fixtures
```
$ python manage.py dumpdata --all --natural-foreign --indent 2 auth.User auth.Group person parliament government document website > website/fixtures/<fixture_name>.json
```

### Debug toolbar

Enable the django debug toolbar by uncommenting the django_toolbar related lines in `INSTALLED_APPS` and `MIDDLEWARE_CLASSES` in `website/settings.py`.

## CronJobs

Openkamer has some optional cronjobs that do some cool stuff. You can review them in `website/cron.py`.  
Create the following cronjob (Linux) to kickstart the `django-cron` jobs,
```
$ crontab -e
*/5 * * * * source /home/<user>/.bashrc && source /home/<path-to-openkamer>/openkamer/env/bin/activate && python /home/<path-to-openkamer>/website/manage.py runcrons > /home/<path-to-openkamer>/log/cronjob.log
```
