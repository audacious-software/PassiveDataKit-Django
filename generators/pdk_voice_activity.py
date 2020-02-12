# pylint: disable=line-too-long, no-member


def generator_name(identifier): # pylint: disable=unused-argument
    return 'Voice Activity Detection'

def extract_secondary_identifier(properties):
    if 'voices_present' in properties:
        if properties['voices_present']:
            return 'present'

        return 'not-present'

    return 'unknown'
