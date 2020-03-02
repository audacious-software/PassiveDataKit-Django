# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-02-21 18:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0079_databundle_errored'),
    ]

    operations = [
        migrations.AddField(
            model_name='deviceissue',
            name='device_performance_related',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deviceissue',
            name='device_stability_related',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deviceissue',
            name='iu_related',
            field=models.BooleanField(default=False),
        ),
    ]