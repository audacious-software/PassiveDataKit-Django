
def extract_secondary_identifier(properties):
    if 'datastream' in properties:
        return properties['datastream']

    return None
