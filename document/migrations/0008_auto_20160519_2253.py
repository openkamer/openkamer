# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-19 20:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0007_auto_20160518_1825'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kamerstuk',
            options={'ordering': ['id_sub'], 'verbose_name_plural': 'Kamerstukken'},
        ),
        migrations.AlterField(
            model_name='kamerstuk',
            name='id_main',
            field=models.CharField(blank=True, default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='kamerstuk',
            name='id_sub',
            field=models.CharField(blank=True, default='', max_length=40),
            preserve_default=False,
        ),
    ]
