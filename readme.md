# Keep Search tool

Keep Search is Python-Flask app that allows to extract queries and pages data from Google Search Console API v3 and store it into a database. 

It has a signup, login (with hash password), capability to clasify your queries by branded vs non-branded, and url_parsed (extract directory from 'page' dimension)

It uses Python 3.6 syntax. You can use it locally or deployed to a server. In my case, I use Google Cloud

columns = "gsc_query, country, date_query, page, device, url_parsed, uri, clicks, impressions, ctr, position, querytype"

This is a very Beta version, but works fine 

## Why to extract GSC data?

Google Search Console has numerous limitations:

•	It stores search queries for a limited period: after 90 days query on previous data is no longer available. 
•	Interface only shows top 1,000 queries.
•	Data can be filtered by device or country, etc., but only one at a time. 
•	Data download is possible to csv files, but this can be time-consuming if this process is required regularly.


## Create a virtualenv

[![How to create a virtualenv]](http://docs.python-guide.org/en/latest/dev/virtualenvs/)

For virtualenv to install all files in the requirements.txt file, you need to activate your virtualenv

## Install all the python libraries included in requirements.txt

cd to the directory where requirements.txt is located, and run following command

```bash
pip install -r requirements.txt
```


### Create a database

This app uses a MySQL database called 'gscusers'. You can use MySQL workbench or the command line

```bash
CREATE DATABASE IF NOT EXISTS gscusers;
```

You can use other database of your choice like Postgres, but you will need to change the config.py file

### Modify config.py file

This file contain the localhost database and the live database. You will need to change the details.


### Run the app

Finally, run `python main.py` to run the app, viewable at this URL:

```
http://localhost:5000
```

