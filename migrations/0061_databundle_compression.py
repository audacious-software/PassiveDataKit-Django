# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-08-05 20:35


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0060_auto_20190620_2326'),
    ]

    operations = [
        migrations.AddField(
            model_name='databundle',
            name='compression',
            field=models.CharField(db_index=True, default='none', max_length=128),
        ),
    ]
