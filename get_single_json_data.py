#!/usr/bin/env python3.5
from argparse import ArgumentParser
from dateutil import parser as DateParser
#from datetime import datetime
#from dateutil.relativedelta import relativedelta

import json
import logging
import api_helper
import sys
import csv

REPORT_JSON_NAME = "minici.json"
REPORT_TEST_UNITS = {"unit01" : {"release" : "12.04.5",
                                 "formfactor" : "desktop",
                                 "canonical_id" : "201302-12843"}}

class Summary(object):
    """
    summary data object
    """
    _excludes = ['__class__',
                 '__delattr__',
                 '__dict__',
                 '__doc__',
                 '__format__',
                 '__getattribute__',
                 '__hash__',
                 '__init__',
                 '__module__',
                 '__new__',
                 '__reduce__',
                 '__reduce_ex__',
                 '__repr__',
                 '__setattr__',
                 '__sizeof__',
                 '__str__',
                 '__subclasshook__',
                 '__weakref__']

    _includes = ['release',
                 'formfactor',
                 'canonical_id',
                 'submission_id',
                 'date',
                 'passed',
                 'failed',
                 'skipped',
                 'total',
                 'checkbox_log_url']


    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if k in self._excludes or not (k in self._includes):
                raise TypeError("{0} is not a valide keyword argument".format(k))
            self.__dict__[k] = v

    def set_fields(self, dict_obj):
        for k in dict_obj.keys():
            self.__dict__.update(dict_obj)

    def get_fields(self):
        return self.__dict__.copy()

class MiniCIReport(object):
    """
    to get mini-CI report
    """
    def __init__(self, api_username, api_key, api_limit):
        self.api_username = api_username
        self.api_key = api_key
        self.api_limit= api_limit
        self.c3api = api_helper.C3api(api_username, api_key, api_limit)

    def get_status_number_date_by_submission_id(self, submission_id):
        data = self.c3api.get_status_number_date_by_submission_id(submission_id)
        return data["passed_test_count"], data["skipped_test_count"], data["failed_test_count"], data["test_count"], DateParser.parse(data["updated_at"]).date().isoformat()

    def write_report(self, summary_report):
        """
        :param summary_report: list contains string in json format
        """
        #output_file = open(self.release + "-" + self.formfactor + "-" + self.canonical_id + ".json","w")
        output_file = open("minici.json","w")
        output_file.write(summary_report)

    def generate_json(self, **kwargs):
        """
        generate data for mini-ci-frontend index.html
        """
        # database: release-fromfactor-canonical_id.minici.dat
        #
        # 110474
        # 110329
        # 110249
        # 110204
        #
        # TODO: How do I know these info?
        # reported by the client and in the database?
        # no I want it in C3
        release = "12.04.5"
        formfactor = "desktop"
        cid = "201302-12843"
        self.release = release
        self.formfactor = formfactor
        self.canonical_id = cid
        summary_report = {"records" : []}
        database = open(release + "-" + formfactor + "-" + cid + ".minici.dat","r")
        for row in csv.DictReader(database):
            summary = Summary(release=release, formfactor=formfactor, canonical_id=cid)
            submission_id = row['submission_id']
            checkbox_log_url = row['checkbox_log_url']
            summary.submission_id = submission_id
            summary.checkbox_log_url = checkbox_log_url
            (summary.passed, summary.skipped, summary.failed, summary.total, summary.date) = self.get_status_number_date_by_submission_id(submission_id)
            summary_report["records"].append(summary.get_fields())

        summary_report_json = json.dumps(summary_report)
        self.write_report(summary_report_json)




def main():
    logging.basicConfig(level=logging.ERROR)

    parser = ArgumentParser("Generates list of new submissions")

    parser.add_argument("-d", "--debug", help="Set debug mode",
                        default=logging.WARNING)
    # Main args
    parser.add_argument('username',
                        help="Launchpad username used to access C3.")
    parser.add_argument('api_key',
                        help="API key used to access C3.")
    parser.add_argument('canonical_id',
                        help="Canonical ID.")
    parser.add_argument('release',
                        help="Ubunutu release, e.g. 14.04.5 LTS.")
    parser.add_argument('form_factor',
                        help="Form factor label on C3, e.g. Desktop or Portable.")
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
    minici_report = MiniCIReport(args.username, args.api_key, args.batch_limit)
    c3_find_filter = {"canonical_id": args.canonical_id,
                      "release": args.release,
                      "form_factor": args.form_factor}
    minici_report.generate_json(c3_find_filter)

if __name__ == "__main__":
    sys.exit(main())
