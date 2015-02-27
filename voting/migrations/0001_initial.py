# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('original_title', models.CharField(max_length=500)),
                ('type', models.CharField(choices=[('AM', 'Amendement'), ('MO', 'Motie'), ('WV', 'Wetsvoorstel')], max_length=2)),
                ('date', models.DateField(auto_now=True)),
                ('document_url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('seats', models.IntegerField()),
                ('url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('decision', models.CharField(choices=[('FO', 'Voor'), ('AG', 'Tegen')], max_length=2)),
                ('details', models.CharField(max_length=2000)),
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
