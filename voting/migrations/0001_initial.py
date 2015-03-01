# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=500)),
                ('original_title', models.CharField(max_length=500, default='', blank=True)),
                ('type', models.CharField(max_length=2, choices=[('AM', 'Amendement'), ('MO', 'Motie'), ('WV', 'Wetsvoorstel')])),
                ('datetime', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('document_url', models.URLField(default='', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('forename', models.CharField(max_length=200)),
                ('surname', models.CharField(max_length=200)),
                ('surname_prefix', models.CharField(max_length=200, default='', blank=True)),
                ('age', models.IntegerField()),
                ('sex', models.CharField(max_length=1, choices=[('M', 'Man'), ('F', 'Vrouw')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=200)),
                ('seats', models.IntegerField()),
                ('url', models.URLField(default='', blank=True)),
                ('icon_url', models.ImageField(upload_to='', blank=True, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('decision', models.CharField(max_length=2, choices=[('FO', 'Voor'), ('AG', 'Tegen')])),
                ('details', models.CharField(max_length=2000, default='', blank=True)),
                ('bill', models.ForeignKey(to='voting.Bill')),
                ('party', models.ForeignKey(to='voting.Party')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='member',
            name='party',
            field=models.ForeignKey(to='voting.Party'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='author',
            field=models.ForeignKey(to='voting.Member'),
            preserve_default=True,
        ),
    ]
