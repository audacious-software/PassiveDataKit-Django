# pylint: disable=line-too-long, no-member

from future import standard_library

try:
    from urllib.parse import urlparse
except ImportError:
    from urllib.parse import urlparse

standard_library.install_aliases()

def generator_name(identifier): # pylint: disable=unused-argument
    return 'PDK mitmproxy Web Visits'

def extract_secondary_identifier(properties):
    if 'url' in properties:
        url = urlparse(properties['url'])

        return url.netloc

    return None
