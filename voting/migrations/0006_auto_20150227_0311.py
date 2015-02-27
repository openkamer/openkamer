# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0005_auto_20150227_0308'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='date',
            new_name='datetime',
        ),
    ]
