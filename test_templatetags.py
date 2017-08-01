# pylint: disable=no-member, line-too-long

from django.template.loader import render_to_string
from django.test import TestCase

from .models import DataSource

class PointsHzTestCase(TestCase):
    def setUp(self):
        DataSource.objects.create(name='PointsHz Test User', identifier='points-hz-test')

    def test_tests_working(self):
        context = {
            'source': DataSource.objects.get(identifier='points-hz-test')
        }

        result = render_to_string('tests/point_hz_test.txt', context)

        self.assertEqual('<span data-toggle="tooltip" data-placement="top" title="     0.000 samples per week">     0.000 mHz</span>', result.strip())

    def tearDown(self):
        DataSource.objects.get(identifier='points-hz-test').delete()
