# pylint: skip-file

# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-07 15:03


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0029_auto_20170829_0147'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportjob',
            name='sequence_count',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='reportjob',
            name='sequence_index',
            field=models.IntegerField(default=1),
        ),
    ]
