#!/usr/bin/python

import httplib2
import urllib.parse as urlparse
import webbrowser
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
import google.oauth2.credentials
import google_auth_oauthlib.flow

def createflow():
	# Copy your credentials from the console
	CLIENT_ID = '87687397921-ojapa7fnl3u8v81sc3v985ia6iqohpfa.apps.googleusercontent.com'
	CLIENT_SECRET = 'wcs7BlftanzlRZvY5b-VcI5D'

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
	
	# Create an httplib2.Http object and authorize it with our credentials
	http = httplib2.Http()
    http = credentials.authorize(http)
    service = build('webmasters', 'v3', http=http)
    return service


def get_properties(service):

	# Retrieve list of properties in account
	site_list = service.sites().list().execute()

	# Filter for verified websites
	verified_sites_urls = [s['siteUrl'] for s in site_list['siteEntry'] if s['permissionLevel'] != 'siteUnverifiedUser' and s['siteUrl'][:4] == 'http']

	return verified_sites_urls