# pylint: disable=no-member, line-too-long

from __future__ import unicode_literals

import calendar
import json

import importlib
from distutils.version import LooseVersion # pylint: disable=no-name-in-module, import-error

import django

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models
from django.db import connection
from django.db.models import Q, QuerySet
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.text import slugify

DB_SUPPORTS_JSON = None
TOTAL_DATA_POINT_COUNT_DATUM = 'Total Data Point Count'
SOURCES_DATUM = 'Data Point Sources'
SOURCE_GENERATORS_DATUM = 'Data Point Source Generator Identifiers'
LATEST_POINT_DATUM = 'Latest Data Point'
GENERATORS_DATUM = 'Data Point Generators'

ALERT_LEVEL_CHOICES = (
    ('info', 'Informative'),
    ('warning', 'Warning'),
    ('critical', 'Critical'),
)


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


class DataPointQuerySet(QuerySet):
    def count(self):
        postgres_engines = ("postgis", "postgresql", "django_postgrespool")
        engine = settings.DATABASES[self.db]["ENGINE"].split(".")[-1]

        is_postgres = engine.startswith(postgres_engines)

        # In Django 1.9 the query.having property was removed and the
        # query.where property will be truthy if either where or having
        # clauses are present. In earlier versions these were two separate
        # properties query.where and query.having

        if LooseVersion(django.get_version()) >= LooseVersion('1.9'):
            is_filtered = self.query.where
        else:
            is_filtered = self.query.where or self.query.having

        if not is_postgres or is_filtered:
            return super(DataPointQuerySet, self).count()

        data_point_count = DataServerMetadatum.objects.filter(key=TOTAL_DATA_POINT_COUNT_DATUM).first()

        if data_point_count is None:
            return super(DataPointQuerySet, self).count()

        return int(data_point_count.value)


class DataPointManager(models.Manager):
    def get_queryset(self):
        return DataPointQuerySet(self.model, using=self._db)

    def sources(self): # pylint: disable=no-self-use
        sources_datum = DataServerMetadatum.objects.filter(key=SOURCES_DATUM).first()

        if sources_datum is not None:
            return json.loads(sources_datum.value)

        sources = DataPoint.objects.order_by().values_list('source').distinct()

        source_ids = []

        for source in sources:
            source_ids.append(source[0])

        sources_datum = DataServerMetadatum(key=SOURCES_DATUM)

        sources_datum.value = json.dumps(source_ids, indent=2)

        sources_datum.save()

        return sources

    def generator_identifiers_for_source(self, source): # pylint: disable=invalid-name, no-self-use
        key = SOURCE_GENERATORS_DATUM + ': ' + source
        sources_datum = DataServerMetadatum.objects.filter(key=key).first()

        identifiers = {}

        if sources_datum is not None:
            identifiers = json.loads(sources_datum.value)

            return identifiers
        else:
            sources_datum = DataServerMetadatum(key=key)

        source_identifiers = DataPoint.objects.filter(source=source).order_by('generator_identifier').values_list('generator_identifier', flat=True).distinct()

        new_identifiers = []

        for identifier in source_identifiers:
            new_identifiers.append(identifier)

        sources_datum.value = json.dumps(new_identifiers, indent=2)

        sources_datum.save()

        return source_identifiers

    def generator_identifiers(self): # pylint: disable=invalid-name, no-self-use
        key = GENERATORS_DATUM
        generators_datum = DataServerMetadatum.objects.filter(key=key).first()

        identifiers = {}

        if generators_datum is not None:
            identifiers = json.loads(generators_datum.value)

            return identifiers
        else:
            generators_datum = DataServerMetadatum(key=key)

        generator_identifiers = DataPoint.objects.all().order_by('generator_identifier').values_list('generator_identifier', flat=True).distinct()

        new_identifiers = []

        for identifier in generator_identifiers:
            new_identifiers.append(identifier)

        generators_datum.value = json.dumps(new_identifiers, indent=2)

        generators_datum.save()

        return generator_identifiers

    def latest_point(self, source, identifier): # pylint: disable=no-self-use
        key = LATEST_POINT_DATUM + ': ' + source + '/' + identifier

        latest_point_datum = DataServerMetadatum.objects.filter(key=key).first()

        latest = None

        if latest_point_datum is not None:
            latest = DataPoint.objects.get(pk=int(latest_point_datum.value))
        else:
            if identifier == 'pdk-data-frequency':
                latest = DataPoint.objects.filter(source=source).order_by('-recorded').first()
            else:
                latest = DataPoint.objects.filter(source=source, generator_identifier=identifier).order_by('-recorded').first()

            if latest is not None:
                latest_point_datum = DataServerMetadatum(key=key)
                latest_point_datum.value = str(latest.pk)
                latest_point_datum.save()

        return latest

    def set_latest_point(self, source, identifier, new_point):
        latest_point = self.latest_point(source, identifier)

        if latest_point is None or latest_point.created < new_point.created:
            key = LATEST_POINT_DATUM + ': ' + source + '/' + identifier

            latest_point_datum = DataServerMetadatum.objects.filter(key=key).first()

            if latest_point_datum is None:
                latest_point_datum = DataServerMetadatum(key=key)

            latest_point_datum.value = str(new_point.pk)
            latest_point_datum.save()


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

    objects = DataPointManager()

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


class DataServerMetadatum(models.Model):
    key = models.CharField(max_length=1024, db_index=True)
    value = models.TextField(max_length=1048576)

    def formatted_value(self): # pylint: disable=no-self-use
        return 'TODO'


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

            duration = (last_point.created - first_point.created).total_seconds()

            if generator['points_count'] > 1 and duration > 0:
                generator['frequency'] = float(generator['points_count']) / duration
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

    def latest_user_agent(self):
        latest_point = self.latest_point()
        
        if latest_point is not None:
			properties = latest_point.fetch_properties()

			if 'passive-data-metadata' in properties:
				if 'generator' in properties['passive-data-metadata']:
					tokens = properties['passive-data-metadata']['generator'].split(':')

					return tokens[-1].strip()

        return None


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


class DataPointVisualization(models.Model):
    source = models.CharField(max_length=1024, db_index=True)
    generator_identifier = models.CharField(max_length=1024, db_index=True)
    last_updated = models.DateTimeField(db_index=True)


class ReportJobManager(models.Manager): # pylint: disable=too-few-public-methods
    def create_jobs(self, user, sources, generators, export_raw=False): # pylint: disable=too-many-locals, too-many-branches, too-many-statements, no-self-use
        batch_request = ReportJobBatchRequest(requester=user, requested=timezone.now())

        params = {}

        params['sources'] = sources
        params['generators'] = generators
        params['export_raw'] = export_raw

        if install_supports_jsonfield():
            batch_request.parameters = params
        else:
            batch_request.parameters = json.dumps(params, indent=2)

        batch_request.save()

class ReportJob(models.Model):
    objects = ReportJobManager()

    requester = models.ForeignKey(settings.AUTH_USER_MODEL)

    requested = models.DateTimeField(db_index=True)
    started = models.DateTimeField(db_index=True, null=True, blank=True)
    completed = models.DateTimeField(db_index=True, null=True, blank=True)

    sequence_index = models.IntegerField(default=1)
    sequence_count = models.IntegerField(default=1)

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

class ReportJobBatchRequest(models.Model):
    requester = models.ForeignKey(settings.AUTH_USER_MODEL)

    requested = models.DateTimeField(db_index=True)
    started = models.DateTimeField(db_index=True, null=True, blank=True)
    completed = models.DateTimeField(db_index=True, null=True, blank=True)

    if install_supports_jsonfield():
        parameters = JSONField()
    else:
        parameters = models.TextField(max_length=(32 * 1024 * 1024 * 1024))

    def process(self): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        self.started = timezone.now()
        self.save()

        target_size = 5000000

        try:
            target_size = settings.PDK_TARGET_SIZE
        except AttributeError:
            pass

        params = None

        if install_supports_jsonfield():
            params = self.parameters
        else:
            params = json.loads(self.parameters)

        generator_query = None

        for generator in params['generators']:
            if generator_query is None:
                generator_query = Q(generator_identifier=generator)
            else:
                generator_query = generator_query | Q(generator_identifier=generator)

        requested = timezone.now()

        source_query = None
        report_size = 0
        report_sources = []

        pending_jobs = []

        sources = sorted(params['sources'], reverse=True)

        while sources:
            source = sources.pop()

            if source_query is None:
                source_query = Q(source=source)
            else:
                source_query = source_query | Q(source=source)

            query_size = DataPoint.objects.filter(generator_query, source_query).count()

            if report_size == 0 or (report_size + query_size) < target_size:
                report_sources.append(source)

                report_size += query_size
            else:
                job = ReportJob(requester=self.requester, requested=requested)

                job_params = {}

                job_params['sources'] = report_sources
                job_params['generators'] = params['generators']
                job_params['raw_data'] = params['export_raw']

                if install_supports_jsonfield():
                    job.parameters = job_params
                else:
                    job.parameters = json.dumps(job_params, indent=2)

                pending_jobs.append(job)

                source_query = None
                report_size = 0
                report_sources = []


        if report_sources and source_query is not None:
            job = ReportJob(requester=self.requester, requested=requested)

            job_params = {}

            job_params['sources'] = report_sources
            job_params['generators'] = params['generators']
            job_params['raw_data'] = params['export_raw']

            if install_supports_jsonfield():
                job.parameters = job_params
            else:
                job.parameters = json.dumps(job_params, indent=2)

            pending_jobs.append(job)

            source_query = None
            report_size = 0
            report_sources = []

        index = 1

        for job in pending_jobs:
            job.sequence_index = index
            job.sequence_count = len(pending_jobs)
            job.save()

            index += 1

        self.completed = timezone.now()
        self.save()
