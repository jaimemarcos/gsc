from flask_sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash

#from urllib import urlopen

import geocoder
import urllib
import requests
import json


db = SQLAlchemy()

class User(db.Model):
  __tablename__ = 'users'
  uid = db.Column(db.Integer, primary_key = True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  pwdhash = db.Column(db.String(54))

  def __init__(self, firstname, lastname, email, password):
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    self.email = email.lower()
    self.set_password(password)
     
  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)


class Authorization(db.Model):
  __tablename__ = 'authorization'
  email = db.Column(db.String(120), primary_key = True)
  project_key = db.Column(db.String(100))
  api_key = db.Column(db.String(100))
  brand_queries = db.Column(db.String(300))


  def __init__(self, email, project_key, api_key, brand_queries):
    self.email = email.lower()
    self.project_key = project_key
    self.api_key  = api_key
    self.brand_queries  = brand_queries
