# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-08 09:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0035_auto_20170308_1023'),
    ]

    operations = [
        migrations.RenameField(
            model_name='antwoord',
            old_name='also_answers_nr',
            new_name='see_answer_nr',
        ),
    ]
