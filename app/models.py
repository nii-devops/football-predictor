from flask_login import UserMixin
from datetime import datetime

# Import db from your app package instead of creating a new instance
from . import db

# Remove EPL_TEAMS from here to avoid circular imports - it's now in forms.py

season_weeks = db.Table('season_weeks',
    db.Column('season_id', db.Integer, db.ForeignKey('season.id'), primary_key=True),
    db.Column('week_id', db.Integer, db.ForeignKey('week.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    def __repr__(self):
        return f'<User {self.email}>'


class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season_start_year = db.Column(db.Integer, nullable=False)
    season_end_year = db.Column(db.Integer, nullable=False)
    match_weeks = db.relationship('MatchWeek', backref='season', lazy=True)


class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    


class MatchWeek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    week_id = db.Column(db.Integer, db.ForeignKey('week.id'), nullable=False)
    week = db.relationship('Week')
    predictions_open_time = db.Column(db.DateTime, nullable=False)
    predictions_close_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    fixtures = db.relationship('Fixture', backref='match_week', lazy=True)
    
    
    def __repr__(self):
        return f'<MatchWeek {self.week_id}: Season {self.season_id}>'
    @property
    def is_predictions_open(self):
        now = datetime.utcnow()
        return self.predictions_open_time <= now <= self.predictions_close_time


class Fixture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_week_id = db.Column(db.Integer, db.ForeignKey('match_week.id'), nullable=False)
    home_team = db.Column(db.String(50), nullable=False)
    away_team = db.Column(db.String(50), nullable=False)
    match_datetime = db.Column(db.DateTime, nullable=True)
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship('Prediction', backref='fixture', lazy=True)
    def __repr__(self):
        return f'<Fixture {self.home_team} vs {self.away_team}>'
    @property
    def result(self):
        if not self.is_completed:
            return None
        if self.home_score > self.away_score:
            return 'H'
        elif self.away_score > self.home_score:
            return 'A'
        else:
            return 'D'


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixture.id'), nullable=False)
    home_score_prediction = db.Column(db.Integer, nullable=False)
    away_score_prediction = db.Column(db.Integer, nullable=False)
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'fixture_id', name='unique_user_fixture'),)
    def __repr__(self):
        return f'<Prediction {self.home_score_prediction}-{self.away_score_prediction}>'
    @property
    def predicted_result(self):
        if self.home_score_prediction > self.away_score_prediction:
            return 'H'
        elif self.away_score_prediction > self.home_score_prediction:
            return 'A'
        else:
            return 'D'


