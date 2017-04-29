
def extract_secondary_identifier(properties):
    if 'event_name' in properties:
        return properties['event_name']

    return None
