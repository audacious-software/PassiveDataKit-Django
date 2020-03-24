# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-24 20:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0081_auto_20200227_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datapoint',
            name='generator',
            field=models.CharField(max_length=1024),
        ),
        migrations.AlterField(
            model_name='datapoint',
            name='source',
            field=models.CharField(max_length=1024),
        ),
        migrations.AlterIndexTogether(
            name='datapoint',
            index_together=set([('generator_definition', 'source_reference'), ('generator_definition', 'source_reference', 'created', 'recorded'), ('generator_definition', 'created'), ('generator_definition', 'source_reference', 'recorded'), ('generator_definition', 'source_reference', 'created'), ('source_reference', 'created')]),
        ),
    ]
