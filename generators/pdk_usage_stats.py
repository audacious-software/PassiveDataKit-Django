# pylint: disable=line-too-long, no-member

def extract_secondary_identifier(properties):
    if 'event_type' in properties:
        return properties['event_type']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Device Usage Events'
