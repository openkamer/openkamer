# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-06 16:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parliament', '0008_commissie'),
        ('document', '0056_auto_20190203_1322'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommissieDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commissie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parliament.Commissie')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='document.Document')),
                ('kamerstuk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='document.Kamerstuk')),
            ],
        ),
    ]