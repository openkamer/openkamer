# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-25 18:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0012_auto_20161125_1707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='besluitenlijst',
            name='commission',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='besluitenlijst',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='besluititemcase',
            name='related_document_ids',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='besluititemcase',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='document',
            name='title_full',
            field=models.CharField(max_length=3000),
        ),
        migrations.AlterField(
            model_name='document',
            name='title_short',
            field=models.CharField(max_length=2000),
        ),
        migrations.AlterField(
            model_name='kamerstuk',
            name='type_long',
            field=models.CharField(blank=True, max_length=2000),
        ),
        migrations.AlterField(
            model_name='kamerstuk',
            name='type_short',
            field=models.CharField(blank=True, max_length=400),
        ),
    ]
