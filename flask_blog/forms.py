


from flask import redirect, url_for
import psycopg2
from flask import Flask,render_template,url_for,flash,redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from flask_bcrypt import Bcrypt
bcrypt= Bcrypt()

class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('sign up')

    def create_user(self):
        conn = psycopg2.connect(
            host="Localhost",
            database="password",
            user="postgres",
            password="GNanthu$2001"
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email = %s",
            (self.email.data,)
        )
        result = cur.fetchone()

        if result is not None:
            flash('Email address already exists','danger')
            return False

        else:
            password_hash = bcrypt.generate_password_hash(self.password.data).decode('utf-8')
        
            cur = conn.cursor()
            cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (self.username.data, self.email.data, password_hash)
            )
            return True
            conn.commit()
            cur.close()
            conn.close()
class LoginForm(FlaskForm):
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('remember me')
    submit = SubmitField('Login')

  

   
    
 



        