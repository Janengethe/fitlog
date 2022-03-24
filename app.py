#!/usr/bin/python3

"""
Module app
Entry Point
"""
from logging import raiseExceptions
from flask import Flask, render_template, url_for, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager
from flask_login import login_required, logout_user, current_user
from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy import desc


app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'gihbugvbkhyguhvbjuh'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    """
    reloads user id stored in the session
    """
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    User model class for the database
    Has Id, username and password columns
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class Workout(db.Model):
    """
    Workout class
    with Id, created_at, exercise, notes and user_id columns
    """
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    exercise = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '[{} : {}]'.format(self.created_at, self.exercise)


class RegisterForm(FlaskForm):
    """
    Form for registration
    Has username, password and submit fields
    """
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(),
                                         Length(min=4, max=20)],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")


def validate_username(self, username):
    """
    Method to validate a user by the username
    """
    existing_user_username = User.query.filter_by(username.username.data).all()
    if existing_user_username:
        raise ValidationError("Username already exist")


class LoginForm(FlaskForm):
    """
    Form for Login
    Has username, password and submit fields
    """
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(),
                                         Length(min=4, max=20)],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


class WorkoutForm(FlaskForm):
    """
    Form for Workout
    Has exercise, notes and submit fields
    """
    exercise = StringField(validators=[InputRequired(),
                                       Length(min=4, max=200)],
                           render_kw={"placeholder": "Exercise"})
    notes = StringField(validators=[InputRequired(),
                                    Length(min=5)],
                        render_kw={"placeholder": "Add Notes"})
    submit = SubmitField("Save")


@app.route('/')
def index():
    """
    Defines index route
    """
    user = current_user
    return render_template('index.html', user=user)


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Defines login route
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    """
    Defines dasboard route
    Returns the number of workout for the user
    """
    user = current_user
    # user = User.query.filter_by(id=id).first()
    num = Workout.query.filter_by(user_id=user.id).count()
    return render_template('dashboard.html', user=user, num=num)


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """
    Defines logout route
    Exits the user
    """
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    """
    Defines registration route
    Takes the credentials of the new user
    """
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('register.html', form=form)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Defines create route
    Returns a template to create a new workout instance
    """
    form = WorkoutForm()
    if request.method == "POST":
        # user_id = current_user
        new = Workout(exercise=form.exercise.data,
                      notes=form.notes.data,
                      user_id=current_user.id)
        db.session.add(new)
        db.session.commit()
        return redirect(url_for('show_all'))
        # print ("user Id is {}".format(user_id))
    return render_template('create.html', form=form)


@app.route('/show_all/')
@login_required
def show_all():
    """
    Defines show_all route
    Returns a list of the user's workouts
    """
    user = current_user
    workout = Workout.query.filter_by(user_id=user.id).order_by(desc(
        'created_at')).all()
    # user = User.query.filter_by(username=username).first_or_404()
    # return (user)
    # new = Workout.query.all()
    # print (workout)
    return render_template('show_all.html', user=user, workout=workout)


# def get_one(id, check_user=True):
#     one = Workout.query.get(id)
#     return (one)


@app.route('/<int:id>/update', methods=['GET', 'POST'])
def update_workout(id):
    """
    Defines update route
    Allows the user to edit a workout
    """
    one = Workout.query.get(id)
    form = WorkoutForm()
    if request.method == "POST":
        new = Workout(exercise=form.exercise.data,
                      notes=form.notes.data,
                      user_id=current_user.id)
        db.session.add(new)
        db.session.commit()
        return redirect(url_for('show_all'))
    return render_template('update.html', one=one)


@app.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """
    Defines delete
    Allows the user to eliminate a workout
    """
    one = Workout.query.get(id)
    db.session.delete(one)
    db.session.commit()
    return redirect(url_for('show_all'))


if __name__ == "__main__":
    app.run(debug=True)
