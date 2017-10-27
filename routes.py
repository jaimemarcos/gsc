from flask import Flask, render_template, request, session, redirect, url_for, flash
from models import db, User, Authorization
from forms import SignupForm, LoginForm, AuthorizationForm, extractForm, GooglecodeForm
from authorize import createflow, authorize, generate_credentials, get_properties
from gscextract import generate_request, execute_request
import requests
import os
import sys
from oauth2client.client import OAuth2WebServerFlow, Storage


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/gscusers'
SQLALCHEMY_TRACK_MODIFICATIONS = False
db.init_app(app)
app.secret_key = "development-key"


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

  form = SignupForm()

  if request.method == "POST":
    if form.validate() == False:
      return render_template('signup.html', form=form)
    else:
      newuser = User(form.first_name.data, form.last_name.data, form.email.data, form.password.data)
      db.session.add(newuser)
      db.session.commit()

      session['email'] = newuser.email
      return redirect(url_for('home'))

  elif request.method == "GET":
    return render_template('signup.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
  if 'email' in session:
    return redirect(url_for('home'))

  form = LoginForm()

  if request.method == "POST":
    if form.validate() == False:
      return render_template("login.html", form=form)
    else:
      email = form.email.data 
      password = form.password.data 

      user = User.query.filter_by(email=email).first()
      if user is not None and user.check_password(password):
        session['email'] = form.email.data
        if os.stat("webmaster_credentials.dat").st_size == 0:
          return redirect(url_for('home'))
        else:
          return redirect(url_for('step2'))
      else:
        return redirect(url_for('login'))

  elif request.method == 'GET':
    return render_template('login.html', form=form)

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
      newautho = Authorization(email,authoform.client_ID.data, authoform.client_secret.data, authoform.brand_queries.data)
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

  propertyform = extractForm()
  propertyform.searchproperty.choices = listofchoices


  if request.method == 'POST':
    if propertyform.validate() == False:
      flash('Form validation not passed')
      return render_template('step3.html', form=propertyform, option_list=option_list)
    else:
      # get the web property, start and end dates from form
      property_uri = propertyform.searchproperty.data
      start_date = propertyform.start_date.data
      end_date = propertyform.end_date.data

      # generate a request to searchanalytics to extract data
      query_response = generate_request(property_uri, start_date, end_date)

      if query_response:
        flash('New entry was successfully posted')

      # return those results
      return render_template('step3.html', form=propertyform, option_list=option_list, query_response=query_response)

  elif request.method == 'GET':
    return render_template("step3.html", form=propertyform, option_list=option_list)


if __name__ == "__main__":
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  app.run(debug=True)