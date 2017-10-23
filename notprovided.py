 #!/usr/bin/python

# -*- coding: utf-8 -*-
# Copyright 2015 Dirk Ceuppens. All Rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# This software integrates large parts from the following scripts:
# - search_analytics_sample.py that can be found on 
#   https://github.com/google/google-api-python-client/blob/master/samples/searchconsole/search_analytics_api_sample.py
# - the code sampe HelloAnalytics.py that can be found on 
#   https://developers.google.com/analytics/devguides/reporting/core/v3/quickstart/service-py
#    
#   These scripts are used under the following licence:
#
#   Copyright 2015 Google Inc. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
To use:
1) Check the detailed instructions on http://www.trackmedia.be/en/blog/getting-rid-of-not-provided.html
2) Run the script in the command-line as shown below.

Sample usage:

  $ python notprovided.py 'https://www.example.com' '2015-05-01'  '2015-05-30'  'xxxxxx'
                            = your site              = start date  = end date    = Google Analytics View ID
'''


import argparse
import csv
import sys

import time
import random
from collections import defaultdict

import logging

import simplejson
import socket
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools


from googleapiclient import sample_tools
from googleapiclient import errors

# Declare command-line flags.
# Parse the arguments in to variables
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('property_uri', type=str,
                       help=('Site or app URI to query data for (including '
                             'trailing slash).'))
argparser.add_argument('start_date', type=str,
                       help=('Start date of the requested date range in '
                             'YYYY-MM-DD format.'))
argparser.add_argument('end_date', type=str,
                       help=('End date of the requested date range in '
                             'YYYY-MM-DD format.'))
argparser.add_argument('view_id', type=str,
                       help=('Analytics View id'))

###### Analytics functions

def get_service(api_name, api_version, scope, key_file_location,
                service_account_email):
  """Get a service that communicates to a Google API.

  Args:
    api_name: The name of the api to connect to.
    api_version: The api version to connect to.
    scope: A list auth scopes to authorize for the application.
    key_file_location: The path to a valid service account p12 key file.
    service_account_email: The service account email address.

  Returns:
    A service that is connected to the specified API.
  """

  f = open(key_file_location, 'rb')
  key = f.read()
  f.close()

  credentials = SignedJwtAssertionCredentials(service_account_email, key,
    scope=scope)

  http = credentials.authorize(httplib2.Http())

  # Build the service object.
  service = build(api_name, api_version, http=http)

  return service


def get_results(service, profile_id,startdate,enddate):
  # Use the Analytics Service Object to query the Core Reporting API
  # for the number of Google sessions within the requested timeframe
  return service.data().ga().get(
      ids='ga:' + profile_id,
      start_date=startdate,
      end_date=enddate,
      metrics='ga:sessions',
      filters='ga:source==google').execute()

def get_landingpages(service, profile_id,startdate,enddate,next_index, max_requests_api):
  # Use the Analytics Service Object to query the Core Reporting API
  # for the number of sessions - bounce% - avg Session DUration - Pageviews/session for each of the landingpages within the requested timeframe
  # Max_results is 1000 if no value is given - the API returns maximum 10.000 results per request
  return service.data().ga().get(
      ids='ga:' + profile_id,
      start_date=startdate,
      end_date=enddate,
      metrics='ga:sessions,ga:bounces,ga:avgSessionDuration,ga:pageviewsPerSession',
      dimensions='ga:landingPagePath',
      sort='-ga:sessions', # sort sessions descending
      filters='ga:source==google',
      max_results= max_requests_api,
      start_index=next_index).execute()
  


def print_results(results):
  # Print data nicely for the user.

  if results:
    print 'View (Profile): %s' % results.get('profileInfo').get('profileName')
    print 'Total Sessions: %s' % results.get('rows')[0][0]

  else:
    print 'No results found'


def save_analytics(response,flags):
  """Saves results in csv file.
  Each row contains landingpage, sessions, bounces
  Args:
    response: The server response to be printed as a table.
    
  """
  
  
  newrows =[]
  
  for row in response:
    url=row[0].encode('utf-8')
    newrow = (url, row[1], row[2], row[3],row[4]) 
    newrows.append(newrow)
    

  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")
  filename = "Landingpage_analytics_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
    
  f = open("./"+filename, 'a')
  
  print "Saving analytics results to %s" % filename
  print "./Landingpage_analytics_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  writer = csv.writer(f)
  
  writer.writerows(newrows)
  f.close()

def print_landingpages(results):
  # Print data nicely for the user.
  if results:
    print 'View (Profile): %s' % results.get('profileInfo').get('profileName')
    print 'Total Google Sessions: %s' % results.get('rows')

  else:
    print 'No results found'


def get_analytics_data(argv,):
  
  flags = argparser.parse_args()

  # Define the auth scopes to request.
  scope = ['https://www.googleapis.com/auth/analytics.readonly']

  # Use the developer console and replace the values with your
  # service account email and relative location of your key file.
  service_account_email = '455813885970-8fo4pv73qg0t2d998lbd6jn8rrbg2tuf@developer.gserviceaccount.com'
  
  key_file_location = './Analytics-b7428c9767fd.p12'

  # Authenticate and construct service.
  service = get_service('analytics', 'v3', scope, key_file_location,
    service_account_email)

  profile = flags.view_id
  
  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")
  

  # Create blank csv file
  f= open("./Landingpage_analytics_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv", 'wt')
  writer = csv.writer(f)
  writer.writerow( ('Landingpage', 'Sessions', 'Bounces', 'avg. Session Duration', 'avg. Pages/Session') )
  f.close()

  max_requests_api = 10000 # The Google Analytics API has a limit of 10.000 requests per call
  max_landingpages_needed = 20000 # If you have more landingpages - this number can be updated
  next_index = 1
  
  print "Requesting first batch of Analytics data "
  # Send the first request to the Analytics API - max. number of requests is limited by the API
  result = get_landingpages(service,profile,flags.start_date,flags.end_date, next_index, min(max_requests_api,max_landingpages_needed))
  
  # Return the total number of landingpages
  total_number_of_pages = result['totalResults'] 
  
  print "Total number of pages %s" % total_number_of_pages

  next_index = result['query']['max-results'] + 1
  landingpages_table = result['rows']
  
  # If the total number of landingpages of analytics is bigger than 10.000 (max. allowed by API) then request next
  # batch of data until we reach the maximum of pages that are required (default: 20.000)
  
  
  maximum_pages = min (max_landingpages_needed,total_number_of_pages)
  while next_index < maximum_pages:
    additional_results = get_landingpages(service,profile,flags.start_date,flags.end_date, next_index, max_requests_api)
    print "Requesting additional data - starting at result %s" %next_index  
    
    next_index = next_index + additional_results['query']['max-results'] 
    
    
    landingpages_table = landingpages_table + additional_results['rows']
    
  save_analytics(landingpages_table,flags)
  landingpages=[] 
  for row in landingpages_table:
    newrow=(flags.property_uri+row[0],row[1],row[2],row[3],row[4])
    landingpages.append(newrow)

  print "Analytics data collected."

  return(landingpages)

####### Search console functions

def get_search_console_data(argv,landingpages):
  service, flags = sample_tools.init(
      argv, 'webmasters', 'v3', __doc__, __file__, parents=[argparser],
      scope='https://www.googleapis.com/auth/webmasters.readonly')
  
  # create initial blank file with title
  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")
  
  f= open("./Landingpage_keyword_"+basic_url+"_"+flags.start_date+"_"+flags.end_date+".csv", 'wt')
  writer = csv.writer(f)
  writer.writerow( ('Keyword', 'Landingpage', 'Clicks', 'Impressions', 'CTR', 'Position') )
  f.close()

  # First run a query to learn which dates we have data for. You should always
  # check which days in a date range have data before running your main query.
  # This query shows data for the entire range, grouped and sorted by day,
  # descending; any days without data will be missing from the results.
  request = {
      'startDate': flags.start_date,
      'endDate': flags.end_date,
      'dimensions': ['date']
  }
  response = execute_request(service, flags.property_uri, request)
  
   
  # Get totals for the date range.
  request = {
      'startDate': flags.start_date,
      'endDate': flags.end_date
  }
  response = execute_request(service, flags.property_uri, request)
  print_table(response, 'Totals')
  
  print "Retrieving top 1000 keywords from search console"
  # Get top queries for the date range, sorted by click count, descending.
  request = {
      'startDate': flags.start_date,
      'endDate': flags.end_date,
      'dimensions': ['query'],
      #'rowLimit': 10
  }
  response = execute_request(service, flags.property_uri, request)
  
  save_table(response, 'Keyword_'+flags.start_date+"_"+flags.end_date+"_"+basic_url,"wt","Keyword")
  print "Done - data saved in "+'Keyword_'+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  
  print "Retrieving top 1000 landingpages from search console"
  # Get top pages for the date range, sorted by click count, descending.
  request = {
      'startDate': flags.start_date,
      'endDate': flags.end_date,
      'dimensions': ['page'],
      #'rowLimit': 10
  }
  response = execute_request(service, flags.property_uri, request)
  
  save_table(response, 'Landingpage_'+flags.start_date+"_"+flags.end_date+"_"+basic_url, "wt","Landingpage")
  print "Done - data saved in "+'Landingpage_'+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  print "Generating Keyword-Landingpage report"
  # Get the Search Console Date for the landingpages retrieved from Analytics

  loop(landingpages,service,flags)

  print "Now checking additional Keywords:"
  get_additional_data(flags,service,"Keyword")
  print "Now checking additional Landingpages"
  get_additional_data(flags,service,"Landingpage")

  # Final step - put all the collected data in one file
  update_file(flags)



def loop(response, service, flags):

  for rij in response:
    page = (rij[0])
    visits = (rij[1])

    if float(visits) >= 5:
      print "Checking result for %s" % page
      #print "visits: %s" % visits

      
      request = {
        'startDate': flags.start_date,
        'endDate': flags.end_date,
        'dimensions': ['query'],
        'dimensionFilterGroups': [{
          'filters': [{
            'dimension': 'page',
            'expression': page
          }]
        }]
      }
      n=0
      request_ok = False

      while (n<10 and not(request_ok)):
        try:
          response = execute_request(service, flags.property_uri, request)
          request_ok= True
          save_global(response, page, flags)
        except errors.HttpError, e:
          n=n+1
          logging.warning("Reason of error %s - page: %s", e, page)

          # Apply exponential backoff.
          time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
          logging.warning("Trying %s of 10 trials", n)
        except socket.error, e:
          n=n+1
          logging.warning("Caught exception socket error: %s - page: %s", e, page)
          time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
          logging.warning("Trying %s of 10 trials", n)
        except Exception as e:     
          n=n+1
          logging.warning("Caught other error")
          logging.error(traceback.format_exc())        
          time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
          logging.warning("Trying %s of 10 trials", n)

      if not(request_ok):
        # If after 10 requests the API fails to return data the script stops
        print "There have been too many errors while trying to contact the API, quitting."
        logging.error("There have been too many errors while trying to contact the API, quitting.")
        sys.exit("Script terminated. Try again later")    


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


def print_table(response, title):
  """Prints out a response table.
  Each row contains key(s), clicks, impressions, CTR, and average position.
  Args:
    response: The server response to be printed as a table.
    title: The title of the table.
  """
  print title + ':'

  if 'rows' not in response:
    return

  rows = response['rows']
  row_format = '{:<20}' + '{:>20}' * 4
  print row_format.format('Keyword', 'Landingpage', 'Clicks', 'Impressions', 'CTR', 'Position')
  for row in rows:
    keys = ''
    # Keys are returned only if one or more dimensions are requested.
    if 'keys' in row:
      keys = u','.join(row['keys']).encode('utf-8')
    print row_format.format(
        keys, row['clicks'], row['impressions'], row['ctr'], row['position'])

def save_global(response, keyword,flags):
  """Saves results in csv file.
  Each row contains kewyord, landingpage, clicks, impressions, CTR, and average position.
  Args:
    response: The server response to be printed as a table.
    
  """
  

  if 'rows' not in response:  
    return

  newrows =[]
  rows = response['rows']
  for row in rows:
    keys = ''
    # Keys are returned only if one or more dimensions are requested.
    if 'keys' in row:
      keys = u','.join(row['keys']).encode('utf-8')
      
    newrow = (keys, keyword, row['clicks'], row['impressions'], row['ctr'], row['position']) 
    newrows.append(newrow)
  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")
  f = open("./Landingpage_keyword_"+basic_url+"_"+flags.start_date+"_"+flags.end_date+".csv", 'a')
  writer = csv.writer(f)
  writer.writerows(newrows)
  f.close()


def save_table(response, title, mode,data_type):
  '''Prints out a response table.

  Each row contains key(s), clicks, impressions, CTR, and average position.

  Args:
    response: The server response to be printed as a table.
    title: The title of the table.
  '''


  if 'rows' not in response:
    return

  rows = response['rows']

  newrows =[]

  for row in rows:
    keys = ''
    # Keys are returned only if one or more dimensions are requested.
    if 'keys' in row:
      keys = u','.join(row['keys']).encode('utf-8')

    newrow = (keys, row['impressions'], row['clicks'], row['position']) 
    newrows.append(newrow)

  f = open("./"+ title + ".csv", mode)  
  writer = csv.writer(f)
  if mode == "wt":  
    writer.writerow( (data_type, 'impressions', 'clicks', 'avg_position') )
  writer.writerows(newrows)
  f.close()

def get_additional_data(flags,service,data_type):
  # First get the keywords from the landingpage - keyword report that have minimum 5 clicks
  # save the results in csv
  # type can be "Keyword" or "Landingpage"
  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")
  
  vol_data=[]
  

  with open("./Landingpage_keyword_"+basic_url+"_"+flags.start_date+"_"+flags.end_date+".csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if float(row['Clicks'])> 1:
        
        vol_data.append(row[data_type])
  # Then get the keywords from the top 1000 queries from Search Console
  initial_data=[]
  
  with open(data_type+"_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      initial_data.append(row[data_type])
 
  # Now - deduplicate the list from the landingpage-keyword report - then delete the keywords/landingpages that have already been queried:
  # Store them in data_to_check
  data_to_check = list(set(vol_data)-set(initial_data))

  if data_type=="Keyword":
      dimension = 'query'
  if data_type=="Landingpage":
      dimension = 'page'
  print dimension
  for rij in data_to_check:
    key = (rij)
    print "Checking data for %s" % key

    
    request = {
      'startDate': flags.start_date,
      'endDate': flags.end_date,
      'dimensions': [dimension],
      'dimensionFilterGroups': [{
        'filters': [{
          'dimension': dimension,
          'expression': key
        }]
      }]
    }

    n=0
    request_ok = False

    while (n<10 and not(request_ok)):
      try:
        response = execute_request(service, flags.property_uri, request)
        save_table(response, data_type+"_"+flags.start_date+"_"+flags.end_date+"_"+basic_url,"a",data_type)
        request_ok= True
      except errors.HttpError, e:
        n=n+1        
        logging.warning("Reason of error %s - data: %s", e, key)
        # Apply exponential backoff.
        time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
        print "Trying %s of 10 trials" % n
        logging.warning("Trying %s of 10 trials", n)
      except socket.error, e:
        n=n+1
        logging.warning("Caught exception socket error: %s - data %s ", e, key)        
        time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
        logging.warning("Trying %s of 10 trials", n)
      except Exception as e:     
        n=n+1
        logging.warning("Caught other error")
        logging.error(traceback.format_exc())        
        time.sleep((2 ** n) + random.randint(0, 1000) / 1000)
        logging.warning("Trying %s of 10 trials", n)


    if not(request_ok):
      print "There have been too many errors while trying to contact the API, quitting."
      logging.error("There have been too many errors while trying to contact the API, quitting.")
      sys.exit("Script terminated. Try again later.")
    
def update_file(flags):
  #Combining all the data previously collected and stored in 3 seperate csv files into one global csv file
  print "Merging files"
  basic_url = flags.property_uri
  basic_url = basic_url.replace("://","_")
  basic_url =basic_url.replace(".","-")  
  
  matchfile ="Landingpage_analytics_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  
  matchfile2 ='Landingpage_'+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  matchfile3 ="Keyword_"+flags.start_date+"_"+flags.end_date+"_"+basic_url+".csv"
  csvfile="Landingpage_keyword_"+basic_url+"_"+flags.start_date+"_"+flags.end_date+".csv"
  newfile="Global_report_"+basic_url+"_"+flags.start_date+"_"+flags.end_date+".csv"
  print matchfile
  print matchfile2
  print matchfile3
  new_data=[] 
  new_data2=[]
  new_data3=[]
  with open(csvfile) as fin, open(matchfile) as fmatch, open(matchfile2) as fmatch2, open(matchfile3) as fmatch3, open(newfile,'wb') as fout:
    reader = csv.reader(fin)
    checker = csv.reader(fmatch)
    checker2 = csv.reader(fmatch2)
    checker3 = csv.reader(fmatch3)
    writer = csv.writer(fout)
    header_reader = next(reader)
    checker.next()
    checker2.next()
    checker3.next()
    header_checker =["Clicks Keyword", "Impressions Keyword","Avg. Pos. Keyword","CTR Keyword","Clicks Landingpage","Impressions Landingpage","Avg. Pos. Landingpage","CTR Landingpage","GA Sessions","GA Bouncerate","GA Avg session duration","GA Avg. Pages/Session"]
    new_header = header_reader + header_checker
    writer.writerow(new_header)
    analytics = {}
    keyword = {}
    landingpage = {}

    for a in checker3:
      keyword[a[0]]=[a[2],a[1],a[3],float(a[2])/float(a[1])]

    for b in checker2:
      landingpage[b[0]]=[b[2],b[1],b[3],float(b[2])/float(b[1])]

    for xl in checker:
      url = flags.property_uri+xl[0]
      analytics[url] = [xl[1],float(xl[2])/float(xl[1]),xl[3],xl[4]]

    for i in reader:
      if i[0] in keyword:
        newrow = i + keyword[i[0]]
      else:
        # if keyword doesn't have specific data
        newrow = i + ['N/A', 'N/A', 'N/A', 'N/A']
      new_data.append(newrow)

    for i in new_data:
      if i[1] in landingpage:
        newrow = i + landingpage[i[1]]
      else:
        # if landingpage doesn't have specific data
        newrow = i + ['N/A', 'N/A', 'N/A', 'N/A']      
      new_data2.append(newrow)


    for i in new_data2:
      if i[1] in analytics:
        newrow = i + analytics[i[1]]
        new_data3.append(newrow)  

    new_data3.sort(key=lambda row: float(row[2]), reverse=True)
    writer.writerows(new_data3)


if __name__ == '__main__':
  logging.basicConfig(filename='notprovided.log', level=logging.WARNING)
  logging.info('Started')
  #get the top landing pages from the Analytics API 
  results = get_analytics_data(sys.argv)
  # Send the landing pages to the Search console API
  get_search_console_data(sys.argv,results)
  logging.info('Finished')