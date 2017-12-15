import os

WEBMASTER_CREDENTIALS_FILE_PATH = "webmaster_credentials.dat"

# output folder for csv files
folder = 'output'

# MySQL database information
 
DBUSER = 'root' # MySQL Username
DBPASSWORD = 'password' # MySQL Password
DBHOST = '127.0.0.1' # MySQL Host
DBPORT = 3306 # MySQL Host Port
DBSCHEMA = 'gscusers' # MySQL Database Name


# There are three different ways to store the data in the application. You can choose 'datastore', 'cloudsql', or 'mongodb'. Be sure to
# configure the respective settings for the one you choose below.  You do not have to configure the other data backends. If unsure, choose
# 'datastore' as it does not require any additional configuration.
DATA_BACKEND = 'cloudsql'

# Google Cloud Project ID. This can be found on the 'Overview' page at # https://console.developers.google.com
PROJECT_ID = 'your-project-id'

# CloudSQL & SQLAlchemy configuration.  Replace the following values the respective values of your Cloud SQL instance.
CLOUDSQL_USER = 'root'
CLOUDSQL_PASSWORD = 'password'
CLOUDSQL_DATABASE = 'gscusers'

# Set this value to the Cloud SQL connection name, e.g. "project:region:cloudsql-instance". You must also update the value in app.yaml.
CLOUDSQL_CONNECTION_NAME = 'logical-utility-185911:europe-west2:gsc-db'

UNIX_SOC = '/tmp/mysql.sock'

# The CloudSQL proxy is used locally to connect to the cloudsql instance.
# To start the proxy, use:
#
#   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
#
# Port 3306 is the standard MySQL port. If you need to use a different port,
# change the 3306 to a different port number.

# Alternatively, you could use a local MySQL instance for testing.
LOCAL_SQLALCHEMY_DATABASE_URI = ('mysql://{user}:{password}@127.0.0.1:3306/{database}').format(user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,database=CLOUDSQL_DATABASE)

# When running on App Engine a unix socket is used to connect to the cloudsql
# instance.
LIVE_SQLALCHEMY_DATABASE_URI = ('mysql://{user}:{password}@localhost/{database}?unix_socket=/cloudsql/{connection_name}').format(user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,database=CLOUDSQL_DATABASE, connection_name=CLOUDSQL_CONNECTION_NAME)


# default config
class BaseConfig(object):
	DEBUG = True
	SECRET_KEY = '\xe1\x89\xa6\xfd\x88\xd6\x9d\xd1j:"dtE\x0b\xea*\xf4\x1c\xcd\xdc\x8e\xa8o'
	if os.environ.get('GAE_INSTANCE'):
		SQLALCHEMY_DATABASE_URI = LIVE_SQLALCHEMY_DATABASE_URI
		UNIX_SOC = '/cloudsql/' + CLOUDSQL_CONNECTION_NAME
		DBHOST = 'localhost'
		DBPORT = 3306
	else:
		SQLALCHEMY_DATABASE_URI = LOCAL_SQLALCHEMY_DATABASE_URI
		UNIX_SOC = '/tmp/mysql.sock'
		DBHOST = '127.0.0.1'
		DBPORT = 3306

class TestConfig(BaseConfig):
	DEBUG = True
	TESTING = True
	WTF_CSRF_ENABLED = False
	SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class DevelopmentConfig(BaseConfig):
	DEBUG = True

class ProductionConfig(BaseConfig):
	DEBUG = False