# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-08 09:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0034_antwoord_is_combined'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='antwoord',
            name='is_combined',
        ),
        migrations.AddField(
            model_name='antwoord',
            name='also_answers_nr',
            field=models.IntegerField(null=True),
        ),
    ]