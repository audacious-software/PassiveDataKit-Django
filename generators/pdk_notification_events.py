# pylint: disable=line-too-long, no-member


def generator_name(identifier): # pylint: disable=unused-argument
    return 'Notification Events'

def extract_secondary_identifier(properties):
    if 'action' in properties:
        return properties['action']

    return None
