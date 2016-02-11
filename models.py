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
    
