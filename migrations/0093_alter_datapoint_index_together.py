# pylint: skip-file
# Generated by Django 3.2.16 on 2023-01-18 22:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0092_permissionssupport'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='datapoint',
            index_together={('created', 'source_reference')},
        ),
    ]
