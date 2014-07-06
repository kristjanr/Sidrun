"""

Created at: 06.07.14

(c) 2014 Funderbeam

"""
import re
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _


class YoutubeURLValidator(URLValidator):
    # TODO Check for 'youtube'
    regex = re.compile(
        r'^(?:http)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    message = _('Enter a valid Youtube URL.')