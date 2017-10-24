#!/usr/bin/python

import httplib2
import urllib.parse as urlparse
import webbrowser
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import google.oauth2.credentials
import google_auth_oauthlib.flow
from models import db, User, Authorization

WEBMASTER_CREDENTIALS_FILE_PATH = "webmaster_credentials.dat"

def createflow(useremail):

	user = Authorization.query.filter_by(email=useremail).first()

 	# Copy your credentials from the console
	#CLIENT_ID = '87687397921-ojapa7fnl3u8v81sc3v985ia6iqohpfa.apps.googleusercontent.com'
	#CLIENT_SECRET = 'wcs7BlftanzlRZvY5b-VcI5D'

	CLIENT_ID = user.project_key
	CLIENT_SECRET = user.api_key

	# Check https://developers.google.com/webmaster-tools/search-console-api-original/v3/ for all available scopes
	OAUTH_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'

	# Redirect URI for installed apps
	REDIRECT_URI = 'http://localhost:5000/step2'

	# Run through the OAuth flow and retrieve credentials
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)

	return flow

def authorize(flow):

	authorize_url = flow.step1_get_authorize_url()
	return authorize_url

def generate_credentials(flow, code):

	credentials = flow.step2_exchange(code)
	
	storage = Storage(WEBMASTER_CREDENTIALS_FILE_PATH)
	storage.put(credentials)
	
	# if credentials is None or credentials.invalid:
	# 	credentials = acquire_new_oauth2_credentials(secrets_file)
	return credentials

def get_properties():

	storage = Storage(WEBMASTER_CREDENTIALS_FILE_PATH)
	credentials = storage.get()

	# Create an httplib2.Http object and authorize it with our credentials
	http = httplib2.Http()
	http = credentials.authorize(http)
	service = build('webmasters', 'v3', http=http)

	# Retrieve list of properties in account
	site_list = service.sites().list().execute()

	# Filter for verified websites
	verified_sites_urls = [s['siteUrl'] for s in site_list['siteEntry'] if s['permissionLevel'] != 'siteUnverifiedUser' and s['siteUrl'][:4] == 'http']

	return verified_sites_urls