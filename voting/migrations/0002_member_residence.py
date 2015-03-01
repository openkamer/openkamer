# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='residence',
            field=models.CharField(default='', blank=True, max_length=200),
            preserve_default=True,
        ),
    ]
