# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-25 18:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0014_auto_20161125_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='content_html',
            field=models.CharField(blank=True, max_length=4000000),
        ),
    ]
