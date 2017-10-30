#!/usr/bin/python
# -*- coding: utf-8 -*-
#

import httplib2
import urllib.parse as urlparse
import webbrowser
import argparse
import sys
from googleapiclient import sample_tools
import shutil
import glob
import os
import re
import time
import datetime
import collections
import MySQLdb
import warnings
import csv
import json
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from flask_sqlalchemy import SQLAlchemy
from flask import session, flash
from models import db, User, Authorization
import config


WEBMASTER_CREDENTIALS_FILE_PATH = "webmaster_credentials.dat"

# output folder for csv files
folder = 'output'

# MySQL database information
 
DBUSER = 'root' # MySQL Username
DBPASSWORD = 'password' # MySQL Password
DBHOST = '127.0.0.1' # MySQL Host
DBPORT = 3306 # MySQL Host Port
DBSCHEMA = 'gscusers' # MySQL Database Name
 
# based on https://bitbucket.org/richardpenman/csv2mysql suppress annoying mysql warnings
# warnings.filterwarnings(action='ignore', category=MySQLdb.Warning)


def dates_gen(start_date, end_date):
    # Generate list of dates in YYYY-MM-DD format from start_date to end_date
    result = [start_date.strftime('%Y-%m-%d')]
    day = start_date

    # start_date = dt.datetime(2012, 12,1)
    # end_date = dt.datetime(2012, 12,5)

    # total_days = (end_date - start_date).days + 1 #inclusive 5 days

    while (day < end_date):
        # one day increment
        day = day + datetime.timedelta(1)
        result.append(day.strftime('%Y-%m-%d'))
    
    return result


def clean_name(str):
  #"Remove http:// and https://"
  str = str.replace('http://', '')
  str = str.replace('https://', 's-')
  str = str.replace('/', '')
  return str

 
def generate_request(property_uri, start_date, end_date):
    
    storage = Storage(WEBMASTER_CREDENTIALS_FILE_PATH)
    credentials = storage.get()

    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build('webmasters', 'v3', http=http)

    # parse start date
    year1, month1, day1 = [int(x) for x in start_date.split('-')]
    start_date = datetime.date(year1, month1, day1)

    # parse end date
    year2, month2, day2 = [int(x) for x in end_date.split('-')]
    end_date = datetime.date(year2, month2, day2)

    dates = dates_gen(start_date, end_date)
    flash('Extracting data for period:', dates)

    # get branded queries from db
    email = session['email']
    queries = Authorization.query.filter_by(email=email).first()
    queriesfromdb = queries.brand_queries.split(',')
    print(queriesfromdb)
    flash('Using the following queries to categorize brand', queriesfromdb)


    # Export to csv: generate a request for each day in range, execute the request and export

    for date in dates:
        print('Processing ' + property_uri + date)
        # Get top queries for the date range, sorted by click count, descending.
        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['query', 'country', 'date', 'page', 'device'],
            'rowLimit': 5000
        }
        # Execute the request and export the data to csv file and load into database
        response = execute_request(service, property_uri, request)

        exportcsv(response, queriesfromdb, property_uri,date)
        print('Wait 1 second')
        time.sleep(1)

    # Call the funtion that will Loop over the csv files and store in db.

    insert_into_db(property_uri)


def insert_into_db(property_uri):

    table_property =  clean_name(property_uri)
    table_property = table_property.replace(".", '_')

    try:
        db2 = MySQLdb.connect(unix_socket = '/tmp/mysql.sock',host=DBHOST, user=DBUSER, passwd=DBPASSWORD, port = DBPORT, db=DBSCHEMA)
        cursor = db2.cursor()
        # create table and if doesn't exist
        cursor.execute('CREATE TABLE IF NOT EXISTS %s;' % table_property)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None

    return
 
    # # define table
    # print('Analyzing column types ...')
    # col_types = get_col_types(input_file)
    # print(col_types)
 
    # header = None
    # for row in csv.reader(open(input_file)):
    #     if header:
    #         cursor.execute(insert_sql, row)
    #     else:
    #         header = [safe_col(col) for col in row]
    #         schema_sql = get_schema(table, header, col_types)
    #         print(schema_sql)
    #         # create table
    #         #cursor.execute('DROP TABLE IF EXISTS %s;' % table)
    #         cursor.execute(schema_sql)
    #         # create index for more efficient access
    #         try:
    #             cursor.execute('CREATE INDEX ids ON %s (id);' % table)
    #         except MySQLdb.OperationalError:
    #             pass # index already exists
 
    #         print('Inserting rows ...')
    #         # SQL string for inserting data
    #         insert_sql = get_insert(table, header)
 
    # # commit rows to database
    # print('Committing rows to database ...')
    # db.commit()


    
def execute_request(service, property_uri, request):
    '''Executes a searchAnalytics.query request.

    Args:
        service: The webmasters service to use when executing the query.
        property_uri: The site or app URI to request data for.
        request: The request to be executed.
 
    Returns:
        An array of response rows.
    '''
    return service.searchanalytics().query(siteUrl=property_uri, body=request).execute()
 
def exportcsv(response, queriesfromdb, property_uri,date):
    '''Prints out a response table.
 
    Each row contains 'query', 'country', 'date', 'clicks', 'impressions', 'ctr', 'position', 'querytype'
 
    Args:
        response: The server response to be printed as a table.
        title: The title of the table.
    '''

    message = ''
 
    if 'rows' not in response:
        message = 'No data for this period. Empty response'
        return message
 
    rows = response['rows']
    row_format = '{:<20}' + '{:>20}' * 4

    # create output folder if not exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # print row_format.format('Keys', 'Clicks', 'Impressions', 'CTR', 'Position')
    # f = open("./TOP_QUERIES.csv", 'a', newline='')
    # writer = csv.writer(f)
    # writer.writerow( ('query', 'country', 'date', 'clicks', 'impressions', 'ctr', 'position', 'querytype') )

    # save as csv
    filename = folder + '/' + clean_name(property_uri) + '-' + date +".csv"
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            for query in queriesfromdb:
                if re.match(row['keys'][0], query):
                    querytype = 'branded'
                    break
                else:
                    querytype = 'non-branded'
            rowtoinsert = (row['keys'][0], row['keys'][1], row['keys'][2], row['keys'][3], row['keys'][4],(urlparse.urlparse(row['keys'][3]).path).split('/')[0], row['clicks'], row['impressions'], round(row['ctr'],2), round(row['position'],2), querytype)  
            print(type(rowtoinsert))       
            writer.writerow(rowtoinsert)

    # for row in rows:
    #     # keys = ''
    #     # # Keys are returned only if one or more dimensions are requested.
    #     # if 'keys' in row:
    #     #     keys = u','.join(row['keys']).encode('utf-8')
    #     # #print row_format.format(keys, row['clicks'], row['impressions'], row['ctr'], row['position'])
    #     for query in queriesfromdb:
    #         if re.match(row['keys'][0], query):
    #             querytype = 'branded'
    #             break
    #         else:
    #             querytype = 'non-branded'            
    #     writer.writerow((row['keys'][0], row['keys'][1], row['keys'][2], row['clicks'], row['impressions'], round(row['ctr'],2), round(row['position'],2), querytype))
    f.close()

    message = 'Your data has been exported to csv file'
    return message