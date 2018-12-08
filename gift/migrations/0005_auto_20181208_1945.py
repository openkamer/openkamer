# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-08 18:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gift', '0004_gift_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gift',
            name='type',
            field=models.CharField(choices=[('BOEK', 'Boek'), ('KAAR', 'Toegangskaart'), ('WIJN', 'Wijn'), ('BLOE', 'Bloemen'), ('PAKK', 'Pakket'), ('DINE', 'Diner'), ('ONB', 'Onbekend')], db_index=True, default='ONB', max_length=4),
        ),
    ]
