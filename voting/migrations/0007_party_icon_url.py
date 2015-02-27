# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0006_auto_20150227_0311'),
    ]

    operations = [
        migrations.AddField(
            model_name='party',
            name='icon_url',
            field=models.ImageField(upload_to='', null=True, blank=True),
            preserve_default=True,
        ),
    ]
