# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_auto_20150227_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='party',
            name='url',
            field=models.URLField(default='', blank=True),
            preserve_default=True,
        ),
    ]
