#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime
from dateutil import parser as DateParser
from dateutil.relativedelta import relativedelta

import json
import requests
import sys

C3_URL = "https://certification.canonical.com"

class C3api(object):
    """
    a helper
    """

    def __init__(self, username, api_key, limit):
        self.username = username
        self.api_key = api_key
        self.limit = limit

    def query(self, endpoint, params=False):

        request_url = C3_URL + endpoint

        request_params = {
            "username": self.username,
            "api_key": self.api_key
        }

        # Update request with optional parameters
        if params:
            request_params.update(params)

        print(request_params)
        result = requests.get(request_url, params=request_params)
        if result.ok:
            # Load web content json as python dict
            try:
                #content = json.loads(result.content)
                content = result.json()
            except ValueError as json_exception:
                print("Failed loading content", json_exception)
                sys.exit(1)
        else:
            # If we dont' get an OK, we need to raise the status error, not eat
            # it silently.
            result.raise_for_status()
            sys.exit(1)

        return content

    def retrieve_machinereports(self, canonical_id, release, from_date):
        """Gather postings from a date range starting with start_date and ending
        with end_date"""

        from_date = string_to_datetime(from_date)
        data = {}
        params = {}

        params['limit'] = self.limit
        params['canonical_id'] = canonical_id
        params['release'] = release
        params['from_date'] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
        data = self.query("/api/v1/machinereports/find/?format=json", params)

        return data


def string_to_datetime(date_string):
    # Converts a string to a datetime object
    return DateParser.parse(date_string)

def main():
    parser = ArgumentParser("Generates list of new submissions")

    # Main args
    parser.add_argument('username',
                        help="Launchpad username used to access C3.")
    parser.add_argument('api_key',
                        help="API key used to access C3.")
    parser.add_argument('canonical_id',
                        help="Canonical ID.")
    parser.add_argument('release',
                        help="Ubunutu release, e.g. 14.04.5 LTS")
    parser.add_argument('--batch_limit', type=int, default=1,
                        help="Number of element in a batch result."
                             " 0 for as many as possible")

    # Date args
    date_args = parser.add_argument_group('Date Options',
        ('Set a date range to retrieve objects.'))
    start_args = date_args.add_mutually_exclusive_group()
    start_args.add_argument('--start', dest='from_date', action='store',
        default=(datetime.now().date() - relativedelta(days=10)).isoformat(),
        help=("The start date for the report in ISO format (YYYY-MM-DD). "
              "By default, objects created after midnight on the start date "
              "specified will be retrieved.  If you wish, you can further "
              "narrow this timeline by adding a time to the start_date in the "
              "ISO format THH:MM:SS, e.g. 2014-04-01T13:30:00 to retrieve "
              "objects created AFTER 1:30PM on April 1 2014. If not used, the "
              "default is ONE day ago: %(default)s. NOTE, this cannot be used "
              "with --oneweek or --onemonth"))
    start_args.add_argument('--oneweek', action='store_true',
        default=False,
        help=("Convenience option. Choosing this will retrieve objects "
              "created in the week before end_date. NOTE, this cannot be used "
              "with --start"))
    start_args.add_argument('--onemonth', action='store_true',
        default=False,
        help=("Same as --oneweek, but retrieves objects created in the month "
              "before end_date.  NOTE, this cannot be used with --start"))

    args = parser.parse_args()
    c3api = C3api(args.username, args.api_key, args.batch_limit)
    content = c3api.retrieve_machinereports(args.canonical_id, args.release, args.from_date)
    from pprint import pprint
    pprint(content)

if __name__ == "__main__":
    sys.exit(main())
