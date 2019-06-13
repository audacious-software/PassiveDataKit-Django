# pylint: disable=line-too-long, no-member

import urlparse

def generator_name(identifier): # pylint: disable=unused-argument
    return 'PDK mitmproxy Web Visits'

def extract_secondary_identifier(properties):
    if 'url' in properties:
        url = urlparse.urlparse(properties['url'])

        return url.netloc

    return None
