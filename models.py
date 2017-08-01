# pylint: disable=no-member, line-too-long

from __future__ import unicode_literals

import calendar
import json

import importlib

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models
from django.db import connection
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.text import slugify

DB_SUPPORTS_JSON = None

def generator_label(identifier):
    for app in settings.INSTALLED_APPS:
        try:
            pdk_api = importlib.import_module(app + '.pdk_api')

            name = pdk_api.name_for_generator(identifier)

            if name is not None:
                return name
        except ImportError:
            pass
        except AttributeError:
            pass

    return identifier

def generator_slugify(str_obj):
    return slugify(str_obj.replace('.', ' ')).replace('-', '_')

def install_supports_jsonfield():
    global DB_SUPPORTS_JSON # pylint: disable=global-statement

    if True and DB_SUPPORTS_JSON is None:
        try:
            DB_SUPPORTS_JSON = connection.pg_version >= 90400
        except AttributeError:
            DB_SUPPORTS_JSON = False

    return DB_SUPPORTS_JSON

class DataPoint(models.Model):
    class Meta: # pylint: disable=old-style-class, no-init, too-few-public-methods
        index_together = [
            ['source', 'created'],
            ['source', 'generator_identifier'],
            ['source', 'generator_identifier', 'created'],
            ['source', 'generator_identifier', 'recorded'],
            ['source', 'generator_identifier', 'created', 'recorded'],
            ['source', 'generator_identifier', 'secondary_identifier'],
            ['source', 'generator_identifier', 'secondary_identifier', 'created'],
            ['source', 'generator_identifier', 'secondary_identifier', 'recorded'],
            ['source', 'generator_identifier', 'secondary_identifier', 'created', 'recorded'],
            ['generator_identifier', 'created'],
            ['generator_identifier', 'recorded'],
            ['generator_identifier', 'created', 'recorded'],
            ['generator_identifier', 'secondary_identifier'],
            ['generator_identifier', 'secondary_identifier', 'created'],
            ['generator_identifier', 'secondary_identifier', 'recorded'],
            ['generator_identifier', 'secondary_identifier', 'created', 'recorded'],
        ]

    source = models.CharField(max_length=1024, db_index=True)
    generator = models.CharField(max_length=1024, db_index=True)
    generator_identifier = models.CharField(max_length=1024, db_index=True, default='unknown-generator')
    secondary_identifier = models.CharField(max_length=1024, db_index=True, null=True, blank=True)

    created = models.DateTimeField(db_index=True)
    generated_at = models.PointField(null=True)

    recorded = models.DateTimeField(db_index=True)

    if install_supports_jsonfield():
        properties = JSONField()
    else:
        properties = models.TextField(max_length=(32 * 1024 * 1024 * 1024))

    def fetch_secondary_identifier(self):
        if self.secondary_identifier is not None:
            return self.secondary_identifier
        else:
            for app in settings.INSTALLED_APPS:
                generator_name = generator_slugify(self.generator_identifier)

                try:
                    generator = importlib.import_module(app + '.generators.' + generator_name)

                    identifier = generator.extract_secondary_identifier(self.fetch_properties())

                    if identifier is not None:
                        self.secondary_identifier = identifier
                        self.save()

                    return self.secondary_identifier
                except ImportError:
                    pass
                except AttributeError:
                    pass

        return None

    def fetch_properties(self):
        if install_supports_jsonfield():
            return self.properties

        return json.loads(self.properties)

class DataBundle(models.Model):
    recorded = models.DateTimeField(db_index=True)

    if install_supports_jsonfield():
        properties = JSONField()
    else:
        properties = models.TextField(max_length=(32 * 1024 * 1024 * 1024))

    processed = models.BooleanField(default=False, db_index=True)

class DataFile(models.Model):
    data_point = models.ForeignKey(DataPoint, related_name='data_files', null=True, blank=True)
    data_bundle = models.ForeignKey(DataBundle, related_name='data_files', null=True, blank=True)

    identifier = models.CharField(max_length=256, db_index=True)
    content_type = models.CharField(max_length=256, db_index=True)
    content_file = models.FileField(upload_to='data_files')

class DataSourceGroup(models.Model):
    name = models.CharField(max_length=1024, db_index=True)

    def __unicode__(self):
        return self.name

class DataSource(models.Model):
    identifier = models.CharField(max_length=1024, db_index=True)
    name = models.CharField(max_length=1024, db_index=True, unique=True)

    group = models.ForeignKey(DataSourceGroup, related_name='sources', null=True, on_delete=models.SET_NULL)

    if install_supports_jsonfield():
        performance_metadata = JSONField(null=True, blank=True)
    else:
        performance_metadata = models.TextField(max_length=(32 * 1024 * 1024 * 1024), null=True, blank=True)

    performance_metadata_updated = models.DateTimeField(db_index=True, null=True, blank=True)

    def __unicode__(self):
        return self.name + ' (' + self.identifier + ')'

    def fetch_performance_metadata(self):
        if self.performance_metadata is not None:
            if install_supports_jsonfield():
                return self.performance_metadata

            return json.loads(self.performance_metadata)

        return {}

    def update_performance_metadata(self):
        metadata = self.fetch_performance_metadata()

        # Update latest_point

        latest_point = DataPoint.objects.filter(source=self.identifier).order_by('-created').first()

        if latest_point is not None:
            metadata['latest_point'] = latest_point.pk

        # Update point_count

        metadata['point_count'] = DataPoint.objects.filter(source=self.identifier).count()

        # Update point_frequency

        if metadata['point_count'] > 1:
            earliest_point = DataPoint.objects.filter(source=self.identifier).order_by('created').first()

            seconds = (latest_point.created - earliest_point.created).total_seconds()

            metadata['point_frequency'] = metadata['point_count'] / seconds
        else:
            metadata['point_frequency'] = 0

        generators = []

        identifiers = DataPoint.objects.filter(source=self.identifier).order_by('generator_identifier').values_list('generator_identifier', flat=True).distinct()

        for identifier in identifiers:
            generator = {}

            generator['identifier'] = identifier
            generator['source'] = self.identifier
            generator['label'] = generator_label(identifier)

            generator['points_count'] = DataPoint.objects.filter(source=self.identifier, generator_identifier=identifier).count()

            first_point = DataPoint.objects.filter(source=self.identifier, generator_identifier=identifier).order_by('created').first()
            last_point = DataPoint.objects.filter(source=self.identifier, generator_identifier=identifier).order_by('-created').first()
            last_recorded = DataPoint.objects.filter(source=self.identifier, generator_identifier=identifier).order_by('-recorded').first()

            generator['last_recorded'] = calendar.timegm(last_recorded.recorded.timetuple())
            generator['first_created'] = calendar.timegm(first_point.created.timetuple())
            generator['last_created'] = calendar.timegm(last_point.created.timetuple())

            if generator['points_count'] > 1:
                generator['frequency'] = float(generator['points_count']) / (last_point.created - first_point.created).total_seconds()
            else:
                generator['frequency'] = 0

            generators.append(generator)

        metadata['generator_statistics'] = generators

        if install_supports_jsonfield():
            self.performance_metadata = metadata
        else:
            self.performance_metadata = json.dumps(metadata, indent=2)

        self.performance_metadata_updated = timezone.now()

        self.save()

    def latest_point(self):
        metadata = self.fetch_performance_metadata()

        if 'latest_point' in metadata:
            return DataPoint.objects.get(pk=metadata['latest_point'])

        return None

    def point_count(self):
        metadata = self.fetch_performance_metadata()

        if 'point_count' in metadata:
            return metadata['point_count']

        return None

    def point_frequency(self):
        metadata = self.fetch_performance_metadata()

        if 'point_frequency' in metadata:
            return metadata['point_frequency']

        return None

    def generator_statistics(self):
        metadata = self.fetch_performance_metadata()

        if 'generator_statistics' in metadata:
            return metadata['generator_statistics']

        return []

ALERT_LEVEL_CHOICES = (
    ('info', 'Informative'),
    ('warning', 'Warning'),
    ('critical', 'Critical'),
)

class DataSourceAlert(models.Model):
    alert_name = models.CharField(max_length=1024)
    alert_level = models.CharField(max_length=64, choices=ALERT_LEVEL_CHOICES, default='info', db_index=True)

    if install_supports_jsonfield():
        alert_details = JSONField()
    else:
        alert_details = models.TextField(max_length=(32 * 1024 * 1024 * 1024))

    data_source = models.ForeignKey(DataSource, related_name='alerts')
    generator_identifier = models.CharField(max_length=1024, null=True, blank=True)

    created = models.DateTimeField(db_index=True)
    updated = models.DateTimeField(null=True, blank=True, db_index=True)

    active = models.BooleanField(default=True, db_index=True)

    def fetch_alert_details(self):
        if install_supports_jsonfield():
            return self.alert_details

        return json.loads(self.alert_details)

    def update_alert_details(self, details):
        if install_supports_jsonfield():
            self.alert_details = details
        else:
            self.alert_details = json.dumps(details, indent=2)

class DataPointVisualizations(models.Model):
    source = models.CharField(max_length=1024, db_index=True)
    generator_identifier = models.CharField(max_length=1024, db_index=True)
    last_updated = models.DateTimeField(db_index=True)


class ReportJob(models.Model):
    requester = models.ForeignKey(settings.AUTH_USER_MODEL)

    requested = models.DateTimeField(db_index=True)
    started = models.DateTimeField(db_index=True, null=True, blank=True)
    completed = models.DateTimeField(db_index=True, null=True, blank=True)

    if install_supports_jsonfield():
        parameters = JSONField()
    else:
        parameters = models.TextField(max_length=(32 * 1024 * 1024 * 1024))

    report = models.FileField(upload_to='pdk_reports', null=True, blank=True)

@receiver(post_delete, sender=ReportJob)
def report_job_post_delete_handler(sender, **kwargs): # pylint: disable=unused-argument
    job = kwargs['instance']

    try:
        storage, path = job.report.storage, job.report.path
        storage.delete(path)
    except ValueError:
        pass
