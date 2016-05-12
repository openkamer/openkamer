#! /bin/bash

source env/bin/activate

python manage.py runserver $1
