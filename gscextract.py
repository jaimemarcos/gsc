import config
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
from flask import session, flash, app
from models import db, User, Authorization, Property


WEBMASTER_CREDENTIALS_FILE_PATH = "webmaster_credentials.dat"



# # database variables
# if os.environ.get('GAE_INSTANCE'):
#     UNIX_SOC = '/cloudsql/' + CLOUDSQL_CONNECTION_NAME
#     DBHOST = 'localhost'
#     DBPORT = 3306
# else:
#     UNIX_SOC = '/tmp/mysql.sock'
#     DBHOST = '127.0.0.1'
#     DBPORT = 3306

# CLOUDSQL_USER = 'root'
# CLOUDSQL_PASSWORD = 'password'
# CLOUDSQL_DATABASE = 'gscusers'

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
  str = str.replace('https://', '')
  str = str.replace('/', '')
  return str


def create_dbconexion():
    try:
        db2 = MySQLdb.connect(unix_socket = config.UNIX_SOC, host=config.DBHOST, user=config.CLOUDSQL_USER, passwd=config.CLOUDSQL_PASSWORD, port = config.DBPORT, db=config.CLOUDSQL_DATABASE)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None
    return db2

def create_table(db2,cursor,property_uri):

    table_property = clean_name(property_uri)
    table_property = table_property.replace(".", '_')

    # Create table as per requirement with the following fields
    # (query, country, date_query, page, device, url_parsed, uri, clicks, impressions, ctr, position, querytype)
    sql = """CREATE TABLE IF NOT EXISTS `%s` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gsc_query VARCHAR(400),
        country VARCHAR(5),
        date_query DATE,
        page VARCHAR(200),
        device VARCHAR(10),
        url_parsed VARCHAR(200),
        uri VARCHAR(200),
        clicks INT,
        impressions INT,
        ctr FLOAT(6,3),
        position FLOAT(6,3),
        querytype VARCHAR(15))""" % (table_property)

    cursor.execute(sql)
    db2.commit()
    return

 
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


    # get branded queries from db
    email = session['email']
    queries = Property.query.filter_by(search_property=property_uri, email=email).first()
    queriesfromdb = queries.brand_queries.split(',')


    db2 = create_dbconexion()
    cursor = db2.cursor()
    create_table(db2,cursor,property_uri)
    tablename = clean_name(property_uri).replace(".", '_')

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

        export_insert(response, queriesfromdb, property_uri,date,cursor,tablename)
        time.sleep(1)

    db2.commit()

    message = 'Your data has been exported'
    return message

    
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
 
def export_insert(response, queriesfromdb, property_uri,date,cursor,tablename):
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
    folder = 'output/' + clean_name(property_uri)
    if not os.path.exists(folder):
        os.makedirs(folder)

    columns = "gsc_query, country, date_query, page, device, url_parsed, uri, clicks, impressions, ctr, position, querytype"

    # createa filename and iterate over the response rows. Insert into csv and db

    for row in rows:
        for query in queriesfromdb:
            if re.search(query,row['keys'][0]):
                querytype = 'branded'
                break
            else:
                querytype = 'non-branded'
        
        # Create row will all the data to insert  into csv and database table named as property
        #if :
        #clean_query = re.sub(r'\ or\ ', ' ', row['keys'][0]) # Found queries with 'or' expresions in search
        # clean_query = re.sub(r'[^0-9a-zA-Z\n]+', '',  str(row['keys'][0]) ) # keep only alphanumeric
        # clean_query = clean_query.replace(' or ', '')
        rowtoinsert = ( re.sub(r'[^0-9a-zA-Z ]+', '', row['keys'][0]) if len(row['keys'][0]) < 100 else re.sub(r'[^0-9a-zA-Z ]+', '', row['keys'][0])[0:100], # clean the query to avoid special characters
                        row['keys'][1], # country
                        row['keys'][2], # date
                        row['keys'][3], # page
                        row['keys'][4], # device
                        'home' if str(row['keys'][3].split(property_uri)[1]).split('/')[0] == '' else str(row['keys'][3].split(property_uri)[1]).split('/')[0],  # url_parsed (urlparse.urlparse(row['keys'][3]).path).split('/')[0],
                        '/' if str(row['keys'][3].split(property_uri)[1]) == '' else '/' + str(row['keys'][3].split(property_uri)[1]), # get the URI
                        row['clicks'], # clicks
                        row['impressions'], # impressions
                        round(row['ctr'],2), # ctr
                        round(row['position'],2), #position
                        querytype)

        # Store into database
        sql = "INSERT INTO %s" % (tablename) + " VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);" 
        cursor.execute(sql, list(rowtoinsert))

    return