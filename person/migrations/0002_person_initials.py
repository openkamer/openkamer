# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-15 09:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='initials',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
