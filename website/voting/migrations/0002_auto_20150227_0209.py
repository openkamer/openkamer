# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='title',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='bill',
            name='document_url',
            field=models.URLField(blank=True, default=''),
            preserve_default=True,
        ),
    ]
