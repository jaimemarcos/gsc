from flask import Flask, render_template, request, session, redirect, url_for
from models import db, User, Authorization, Place
from forms import SignupForm, LoginForm, AuthorizationForm, extractForm, GooglecodeForm
from authorize import createflow, authorize, generate_credentials, get_properties
import requests
import os
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
        return redirect(url_for('home'))
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

  flow = createflow()
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
  propertyform = extractForm()
  

  if request.method == 'POST':
    if dateform.validate() == False:
      return render_template('step3.html', form=propertyform)
    else:
      # get the property after user authorize

      # get the start and end dates from form
      searchproperty = propertyform.searchproperty.data
      stardate = propertyform.start_date.data
      enddate = propertyform.start_date.data

      # save the keys into database
      pass

  elif request.method == 'GET':
    return render_template("step3.html", form=propertyform, option_list=option_list)


if __name__ == "__main__":
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  app.run(debug=True)