#!/usr/bin/python
# -*- coding: utf-8 -*-
#

"""
Sample usage:
  $ python download.py 2015-06-30
"""

# output folder
folder = 'output'

import argparse, sys, os, json, datetime, time, csv, codecs, cStringIO, io
from googleapiclient import sample_tools

# make sure unicode is ok
reload(sys)  
sys.setdefaultencoding('utf8')

# list of search types
search_types = [
      'image',
      'video',
      'web'
]

# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('start_date', type=str,
                       help=('Start date of the requested date range in '
                             'YYYY-MM-DD format.'))

def dates_gen(start_date):
  'Generate list of dates in YYYY-MM-DD format from start_date to today'
  result = [start_date.strftime('%Y-%m-%d')]
  day = start_date
  while (day < datetime.date.today()):
    # one day increment
    day = day + datetime.timedelta(1)
    result.append(day.strftime('%Y-%m-%d'))
  return result

def clean_name(str):
  "Remove http:// and https://"
  str = str.replace('http://', '')
  str = str.replace('https://', 's-')
  str = str.replace('/', '')
  return str

def clean_out(x):
  "Clean up for csv"
  x[0] = x[0][0]
  x = [str(i) for i in x]
  return x

def main(argv):

  service, flags = sample_tools.init(
      argv, 'webmasters', 'v3', __doc__, __file__, parents=[argparser],
      scope='https://www.googleapis.com/auth/webmasters.readonly')

  # get all verified properties
  siteEntry = service.sites().list().execute()
  properties = [s['siteUrl'] for s in siteEntry['siteEntry'] if s['permissionLevel'] != 'siteUnverifiedUser']

  # parse start date
  year, month, day = [int(x) for x in flags.start_date.split('-')]
  start_date = datetime.date(year, month, day)

  dates = dates_gen(start_date)

  # create output folder if not exists
  if not os.path.exists(folder):
      os.makedirs(folder)

  for web_property in properties:
    for search_type in search_types:
      for date in dates:

        print 'Processing ' + web_property + ' ' + search_type + ' ' + date
        # Get top queries for the date range, sorted by click count, descending.
        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['query'],
            'searchType': search_type,
            'rowLimit': 5000
        }
        response = execute_request(service, web_property, request)
        print 'Wait 1 second'
        time.sleep(1)

        if 'rows' not in response:
          print 'Empty response.'
          continue

        # save as csv
        filename = folder + '/' + clean_name(web_property) + '-' + search_type + '-' + date +".csv"
        with open(filename, 'wb') as fp:
            header = response['rows'][0].keys()
            rows = [clean_out(r.values()) for r in response['rows']]
            a = csv.writer(fp)
            a.writerow(header)
            a.writerows(rows)

def execute_request(service, property_uri, request):
  """Executes a searchAnalytics.query request.

  Args:
    service: The webmasters service to use when executing the query.
    property_uri: The site or app URI to request data for.
    request: The request to be executed.

  Returns:
    An array of response rows.
  """
  return service.searchanalytics().query(
      siteUrl=property_uri, body=request).execute()

if __name__ == '__main__':
  main(sys.argv)