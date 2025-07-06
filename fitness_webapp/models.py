from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_data = db.relationship('UserData', backref='user', uselist=False)
    workouts = db.relationship('Workout', backref='user', lazy=True)
    weight_tracking = db.relationship('WeightTracking', backref='user', lazy=True)
    body_fat_tracking = db.relationship('BodyFatTracking', backref='user', lazy=True)
    hydration_tracking = db.relationship('HydrationTracking', backref='user', lazy=True)
    hydration_goal = db.relationship('HydrationGoal', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserData(db.Model):
    __tablename__ = 'user_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_fat = db.Column(db.Float)
    gender = db.Column(db.String(20), nullable=False)
    activity_level = db.Column(db.String(100), nullable=False)
    fitness_goal = db.Column(db.String(100), nullable=False)
    goal_weight = db.Column(db.Float)
    goal_body_fat = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Workout(db.Model):
    __tablename__ = 'workouts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    exercise = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Workout {self.exercise} on {self.date}>'

class ExerciseLibrary(db.Model):
    __tablename__ = 'exercise_library'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    muscle_group = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class BodyFatTracking(db.Model):
    __tablename__ = 'body_fat_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body_fat = db.Column(db.Float, nullable=False)
    goal_body_fat = db.Column(db.Float)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    neck_circumference = db.Column(db.Float)
    waist_circumference = db.Column(db.Float)
    hip_circumference = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeightTracking(db.Model):
    __tablename__ = 'weight_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HydrationTracking(db.Model):
    __tablename__ = 'hydration_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    time_of_day = db.Column(db.String(50))
    notes = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HydrationGoal(db.Model):
    __tablename__ = 'hydration_goals'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    daily_goal = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 