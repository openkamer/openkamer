# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-07 20:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0029_vraag'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Antwoord',
            new_name='Kamerantwoord',
        ),
    ]
