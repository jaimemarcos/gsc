from flask_wtf import Form 
from wtforms import StringField, PasswordField, SubmitField, SelectField, validators
from wtforms.validators import DataRequired, Email, Length

class SignupForm(Form):
  first_name = StringField('First name', validators=[DataRequired("Please enter your first name.")])
  last_name = StringField('Last name', validators=[DataRequired("Please enter your last name.")])
  email = StringField('Email', validators=[DataRequired("Please enter your email address."), Email("Please enter your email address.")])
  password = PasswordField('Password', validators=[DataRequired("Please enter a password."), Length(min=6, message="Passwords must be 6 characters or more.")])
  submit = SubmitField('Sign up')

class LoginForm(Form):
  email = StringField('Email', validators=[DataRequired("Please enter your email address."), Email("Please enter your email address.")])
  password = PasswordField('Password', validators=[DataRequired("Please enter a password.")])
  submit = SubmitField("Sign in")

class AuthorizationForm(Form):
  client_ID = StringField('Google Project ID', validators=[DataRequired("Please enter your email address.")])
  client_secret = StringField('API key', validators=[DataRequired("Please enter your API key.")])
  brand_queries = StringField('Brand queries', validators=[DataRequired("Please enter your brand queries separated by commas.")])
  submit = SubmitField("Save")

class GooglecodeForm(Form):
  google_code = StringField('Google Code', validators=[DataRequired("Please copy and enter your Google toke from 'code parameter' within the URL.")])
  submit = SubmitField("Send code to create credentials")

class extractForm(Form):
  searchproperty = SelectField(u'Select a Property')
  start_date = StringField('Start date', validators=[DataRequired("Please enter a start date."), Length(min=10, max=10)])
  end_date = StringField('End date', validators=[DataRequired("Please enter a start date."), Length(min=10, max=10)])
  submit = SubmitField("Submit")