import arrow

from django import template
from django.template.loader import render_to_string
from django.utils import timezone

register = template.Library()

@register.tag(name="sources_table")
def sources_table(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, query = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return SourcesTableNode(query)

class SourcesTableNode(template.Node):
    def __init__(self, query):
        self.query = template.Variable(query)

    def render(self, context):
        query = self.query.resolve(context)

        context['sources'] = query

        return render_to_string('tag_sources_table.html', context)


@register.tag(name="latest_point")
def latest_point(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" %
                                           token.contents.split()[0])

    return LatestPointNode(source)

class LatestPointNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['latest_point'] = source.latest_point()

        return render_to_string('tag_latest_point.html', context)


@register.tag(name="point_count")
def point_count(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return PointCountNode(source)

class PointCountNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        return source.point_count()


@register.tag(name="point_hz")
def point_hz(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return PointHzNode(source)

class PointHzNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        frequency = source.point_frequency()

        value = "{:10.3f}".format(frequency) + " Hz"

        if frequency < 1.0:
            value = "{:10.3f}".format(frequency * 1000) + " mHz"

        tooltip = "{:10.3f}".format(frequency) + " samples per second"

        if frequency < 1.0:
            frequency *= 60

            if frequency > 1.0:
                tooltip = "{:10.3f}".format(frequency) + " samples per minute"
            else:
                frequency *= 60

                if frequency > 1.0:
                    tooltip = "{:10.3f}".format(frequency) + " samples per hour"
                else:
                    frequency *= 24

                    if frequency > 1.0:
                        tooltip = "{:10.3f}".format(frequency) + " samples per day"
                    else:
                        frequency *= 7

                        tooltip = "{:10.3f}".format(frequency) + " samples per week"

        context['value'] = value
        context['tooltip'] = tooltip

        return render_to_string('tag_point_hz.html', context)

@register.tag(name="to_hz")
def to_hz(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, frequency = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return ToHzNode(frequency)

class ToHzNode(template.Node):
    def __init__(self, frequency):
        self.frequency = template.Variable(frequency)

    def render(self, context):
        frequency = self.frequency.resolve(context)

        value = "{:10.3f}".format(frequency) + " Hz"

        if frequency < 1.0:
            value = "{:10.3f}".format(frequency * 1000) + " mHz"

        tooltip = "{:10.3f}".format(frequency) + " samples per second"

        if frequency < 1.0:
            frequency *= 60

            if frequency > 1.0:
                tooltip = "{:10.3f}".format(frequency) + " samples per minute"
            else:
                frequency *= 60

                if frequency > 1.0:
                    tooltip = "{:10.3f}".format(frequency) + " samples per hour"
                else:
                    frequency *= 24

                    if frequency > 1.0:
                        tooltip = "{:10.3f}".format(frequency) + " samples per day"
                    else:
                        frequency *= 7

                        tooltip = "{:10.3f}".format(frequency) + " samples per week"

        context['value'] = value
        context['tooltip'] = tooltip

        return render_to_string('tag_point_hz.html', context)

@register.tag(name="date_ago")
def date_ago(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, date_obj = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return DateAgoNode(date_obj)

class DateAgoNode(template.Node):
    def __init__(self, date_obj):
        self.date_obj = template.Variable(date_obj)

    def render(self, context):
        date_obj = self.date_obj.resolve(context)

        if date_obj is None:
            return 'None'

        now = timezone.now()

        diff = arrow.get(now.isoformat()).datetime - arrow.get(date_obj.isoformat()).datetime

        ago_str = 'Unknown'

        if diff.days > 0:
            ago_str = str(diff.days) + 'd'
        else:
            minutes = diff.seconds / 60

            if minutes >= 60:
                ago_str = str(minutes / 60) + 'h'
            else:
                ago_str = str(minutes) + 'm'

        context['ago'] = ago_str
        context['date'] = date_obj

        return render_to_string('tag_date_ago.html', context)


@register.tag(name="human_duration")
def tag_human_duration(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, seconds_obj = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return HumanDurationNode(seconds_obj)

class HumanDurationNode(template.Node):
    def __init__(self, seconds_obj):
        self.seconds_obj = template.Variable(seconds_obj)

    def render(self, context):
        seconds_obj = self.seconds_obj.resolve(context)

        if seconds_obj is None:
            return ''

        ago_str = str(seconds_obj) + 's'

        if seconds_obj > (24.0 * 60 * 60):
            ago_str = "{0:.2f}".format(seconds_obj / (24.0 * 60 * 60)) + 'd'
        elif seconds_obj > (60.0 * 60):
            ago_str = "{0:.2f}".format(seconds_obj / (60.0 * 60)) + 'h'
        elif seconds_obj > 60.0:
            ago_str = "{0:.2f}".format(seconds_obj / 60.0) + 'm'

        context['human_duration'] = ago_str
        context['seconds'] = seconds_obj

        return render_to_string('tag_human_duration.html', context)


@register.tag(name="generators_table")
def generators_table(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return GeneratorsTableNode(source)

class GeneratorsTableNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['source'] = source

        return render_to_string('tag_generators_table.html', context)


@register.tag(name="generator_label")
def generator_label(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, generator_id = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return GeneratorLabelNode(generator_id)

class GeneratorLabelNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['source'] = source

        return render_to_string('tag_generators_table.html', context)
