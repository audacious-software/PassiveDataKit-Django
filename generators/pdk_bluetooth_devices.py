# pylint: disable=line-too-long, no-member


def generator_name(identifier): # pylint: disable=unused-argument
    return 'Bluetooth Devices'

def extract_secondary_identifier(properties):
    if 'device_class' in properties:
        return properties['device_class']

    return None
