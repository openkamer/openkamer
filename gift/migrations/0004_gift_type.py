# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-08 18:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gift', '0003_remove_personposition_government_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='gift',
            name='type',
            field=models.CharField(choices=[('BOEK', 'Boek'), ('KAART', 'Toegangskaart'), ('WIJN', 'Wijn'), ('DINE', 'Diner'), ('ONB', 'Onbekend')], db_index=True, default='ONB', max_length=4),
        ),
    ]
