from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models

class DataPoint(models.Model):
    source = models.CharField(max_length=1024, db_index=True)
    generator = models.CharField(max_length=1024, db_index=True)
    
    created = models.DateTimeField(db_index=True)
    generated_at = models.PointField(null=True)
    
    recorded = models.DateTimeField(db_index=True)
    
    properties = JSONField()
    
    
class DataBundle(models.Model):
    recorded = models.DateTimeField(db_index=True)
    properties = JSONField()
    
    processed = models.BooleanField(default=False, db_index=True)


class DataSourceGroup(models.Model):
    name = models.CharField(max_length=1024, db_index=True)        

    def __unicode__(self):
        return self.name


class DataSource(models.Model):
    identifier = models.CharField(max_length=1024, db_index=True)
    name = models.CharField(max_length=1024, db_index=True, unique=True)
    
    group = models.ForeignKey(DataSourceGroup, related_name='sources', null=True, on_delete=models.SET_NULL)
    
    def __unicode__(self):
        return self.name + ' (' + self.identifier + ')'
        
    def latest_point(self):
        return DataPoint.objects.filter(source=self.identifier).order_by('-created').first()
    
    def point_count(self):
        return DataPoint.objects.filter(source=self.identifier).count()
        
    def point_frequency(self):
        count = self.point_count()
        
        if count > 0:
            first = DataPoint.objects.filter(source=self.identifier).order_by('created').first()
            last = DataPoint.objects.filter(source=self.identifier).order_by('created').last()
            
            seconds = (last.created - first.created).total_seconds()
            
            return count / seconds
            
        return 0
    