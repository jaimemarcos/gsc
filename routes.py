from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Authorization, Property
from forms import SignupForm, LoginForm, AuthorizationForm, ExtractForm, GooglecodeForm
from authorize import createflow, authorize, generate_credentials, get_properties
from gscextract import generate_request, execute_request
import requests
import os
import sys
from oauth2client.client import OAuth2WebServerFlow, Storage
import config

app = Flask(__name__)
app.secret_key = "development-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/gscusers'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://login:pass@localhost/gscusers'

db.init_app(app)


@app.route("/")
def index():
  return render_template("index.html")

@app.route("/about")
def about():
  return render_template("about.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
  if 'email' in session:
    return redirect(url_for('home'))

  error = None
  form = SignupForm()

  if request.method == "POST":
    if form.validate() == False:
      return render_template('signup.html', form=form)
    else:
      db.create_all()
      flash('User created. Please, login now!')
      newuser = User(form.first_name.data, form.last_name.data, form.email.data, form.password.data)
      db.session.add(newuser)
      db.session.commit()

      return redirect(url_for('login'))

  elif request.method == "GET":
    return render_template('signup.html', form=form, error = error)

@app.route("/login", methods=["GET", "POST"])
def login():
  if 'email' in session:
    return redirect(url_for('home'))

  error = None
  form = LoginForm()

  if request.method == "POST":
    if form.validate() == False:
      flash('Invalid username or password. Please try again! Did you sign up before?') 
      return redirect(url_for('login'))
    else:
      email = form.email.data 
      password = form.password.data 

      user = User.query.filter_by(email=email).first()
      if user is not None and user.check_password(password):
        session['email'] = form.email.data
        authorize = Authorization.query.filter_by(email=email).first()
        if authorize is None:
          return redirect(url_for('home'))
        else:
          return redirect(url_for('step2'))
      else:
        flash('There is no user with those details')
        return redirect(url_for('login'))

  elif request.method == 'GET':
    return render_template('login.html', form=form, error = error)

@app.route("/logout")
def logout():
  session.pop('email', None)
  return redirect(url_for('index'))

@app.route("/home", methods=["GET", "POST"])
def home():
  if 'email' not in session:
    return redirect(url_for('login'))

  authoform = AuthorizationForm()

  if request.method == 'POST':
    if authoform.validate() == False:
      flash('Not valid form')
      return render_template('home.html', form=authoform)
    else:
      # get the project and API key
      email = session['email']

      # save the keys into database
      newautho = Authorization(email,authoform.client_ID.data, authoform.client_secret.data)
      db.session.add(newautho)
      db.session.commit()

      return redirect(url_for('step2'))

  elif request.method == 'GET':
    return render_template("home.html", form=authoform)


@app.route("/step2", methods=["GET", "POST"])
def step2():
  if 'email' not in session:
    return redirect(url_for('login'))

  useremail = session['email']
  flow = createflow(useremail)
  authorizeURL = authorize(flow)
  codeform = GooglecodeForm()

  if request.method == 'POST':
    if codeform.validate() == False:
      return render_template('step2.html', form=codeform)
    else:
      # get the google code form the from
      google_code = codeform.google_code.data

      # generate the credentials
      credentials = generate_credentials(flow, google_code)

    return redirect(url_for('step3'))

  elif request.method == 'GET':
    return render_template("step2.html", authorizeURL=authorizeURL, form=codeform)

@app.route("/step3", methods=["GET", "POST"])
def step3():
  if 'email' not in session:
    return redirect(url_for('login'))

  option_list = get_properties()
  option_list2 = list(option_list)
  listofchoices = list(zip(option_list,option_list2))

  propertyform = ExtractForm()
  propertyform.search_property.choices = listofchoices

  useremail = session['email']

  propertyindb = Property.query.with_entities(Property.search_property,Property.brand_queries).filter_by(email=useremail).all()



  if request.method == 'POST':
    if propertyform.validate() == False:
      flash('Form validation not passed')
      return render_template('step3.html', form=propertyform, option_list=option_list)
    else:

      # get the project and API key
      email = session['email']

      propertyindb = Property.query.filter_by(search_property=propertyform.search_property.data).first()
      
      if propertyindb is None:
        # save the keys into database
        newautho = Property(propertyform.search_property.data, propertyform.brand_queries.data,email)
        db.session.add(newautho)
        db.session.commit()
      else:
        propertyindb.brand_queries = propertyform.brand_queries.data
        db.session.commit()

      # get the web property, start and end dates from form
      property_uri = propertyform.search_property.data
      start_date = propertyform.start_date.data
      end_date = propertyform.end_date.data

      # generate a request to searchanalytics to extract data
      query_response = generate_request(property_uri, start_date, end_date)

      if query_response:
        flash(query_response)

      propertyindb = Property.query.with_entities(Property.search_property,Property.brand_queries).filter_by(email=useremail).all()
      
      # return those results
      return render_template('step3.html', form=propertyform, option_list=option_list, query_response=query_response, branded_queries=propertyindb)

  elif request.method == 'GET':
    return render_template("step3.html", form=propertyform, option_list=option_list, branded_queries=propertyindb)


if __name__ == "__main__":
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  app.run(debug=True)