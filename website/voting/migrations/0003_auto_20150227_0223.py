# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_auto_20150227_0209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='original_title',
            field=models.CharField(default='', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='vote',
            name='details',
            field=models.CharField(default='', max_length=2000, blank=True),
            preserve_default=True,
        ),
    ]
