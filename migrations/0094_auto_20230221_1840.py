# pylint: skip-file
# Generated by Django 3.2.17 on 2023-02-21 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0093_alter_datapoint_index_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportjob',
            name='priority',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='reportjobbatchrequest',
            name='priority',
            field=models.IntegerField(default=0),
        ),
    ]