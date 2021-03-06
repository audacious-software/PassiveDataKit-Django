# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-15 21:32


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0069_auto_20190915_1605'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=1024, unique=True)),
                ('upload_url', models.URLField(db_index=True, max_length=1024, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='datasource',
            name='server',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sources', to='passive_data_kit.DataServer'),
        ),
    ]
