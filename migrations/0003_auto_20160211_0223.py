# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-11 02:23
# pylint: skip-file



from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0002_databundle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databundle',
            name='processed',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='databundle',
            name='recorded',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='datapoint',
            name='created',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='datapoint',
            name='generator',
            field=models.CharField(db_index=True, max_length=1024),
        ),
        migrations.AlterField(
            model_name='datapoint',
            name='recorded',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='datapoint',
            name='source',
            field=models.CharField(db_index=True, max_length=1024),
        ),
    ]
