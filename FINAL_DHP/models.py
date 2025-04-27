from app import db
from flask_login import UserMixin
from datetime import datetime


from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AQIData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    aqi_value = db.Column(db.Float)
    aqi_category = db.Column(db.String(50))
    pm25_value = db.Column(db.Float)
    pm25_category = db.Column(db.String(50))
    pm10_value = db.Column(db.Float)
    pm10_category = db.Column(db.String(50))
    o3_value = db.Column(db.Float)
    o3_category = db.Column(db.String(50))
    no2_value = db.Column(db.Float)
    no2_category = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    continent = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CountryAQI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer)
    avg_aqi = db.Column(db.Float)
    jan = db.Column(db.Float)
    feb = db.Column(db.Float)
    mar = db.Column(db.Float)
    apr = db.Column(db.Float)
    may = db.Column(db.Float)
    jun = db.Column(db.Float)
    jul = db.Column(db.Float)
    aug = db.Column(db.Float)
    sep = db.Column(db.Float)
    oct = db.Column(db.Float)
    nov = db.Column(db.Float)
    dec = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CityAQI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    jan = db.Column(db.Float)
    feb = db.Column(db.Float)
    mar = db.Column(db.Float)
    apr = db.Column(db.Float)
    may = db.Column(db.Float)
    jun = db.Column(db.Float)
    jul = db.Column(db.Float)
    aug = db.Column(db.Float)
    sep = db.Column(db.Float)
    oct = db.Column(db.Float)
    nov = db.Column(db.Float)
    dec = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
