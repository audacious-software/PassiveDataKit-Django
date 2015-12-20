from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models

class DataPoint(models.Model):
    source = models.CharField(max_length=1024)
    generator = models.CharField(max_length=1024)
    
    created = models.DateTimeField()
    generated_at = models.PointField(null=True)
    
    recorded = models.DateTimeField()
    
    properties = JSONField()
    
    