# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_member_residence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='residence',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='member',
            name='surname_prefix',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
            preserve_default=True,
        ),
    ]
