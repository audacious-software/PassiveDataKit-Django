# pylint: skip-file
# Generated by Django 4.2.10 on 2024-03-08 20:18

import sys

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0097_alter_appconfiguration_options'),
    ]

    if sys.version_info[0] > 2:
        operations = [
            migrations.AlterField(
                model_name='appconfiguration',
                name='configuration_json',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='databundle',
                name='properties',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='datapoint',
                name='properties',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='datasource',
                name='performance_metadata',
                field=models.JSONField(blank=True, null=True),
            ),
            migrations.AlterField(
                model_name='datasourcealert',
                name='alert_details',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='reportdestination',
                name='parameters',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='reportjob',
                name='parameters',
                field=models.JSONField(),
            ),
            migrations.AlterField(
                model_name='reportjobbatchrequest',
                name='parameters',
                field=models.JSONField(),
            ),
        ]
    else:
        operations = []
