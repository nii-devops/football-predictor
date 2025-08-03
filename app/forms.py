from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DateTimeField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime

# Move EPL_TEAMS here to avoid circular import
EPL_TEAMS = [
    'Arsenal', 'Aston Villa', 'Brighton & Hove Albion', 'Burnley', 'Chelsea',
    'Crystal Palace', 'Everton', 'Fulham', 'Liverpool', 'Luton Town',
    'Manchester City', 'Manchester United', 'Newcastle United', 'Nottingham Forest',
    'Sheffield United', 'Tottenham Hotspur', 'West Ham United', 'Wolverhampton Wanderers',
    'AFC Bournemouth', 'Brentford'
]

this_year = datetime.now().year


class FixtureForm(FlaskForm):
    class Meta:
        # Disable CSRF for this form since it's used within a FieldList
        csrf = False
    
    home_team = SelectField('Home Team', choices=[(team, team) for team in EPL_TEAMS], validators=[DataRequired()])
    away_team = SelectField('Away Team', choices=[(team, team) for team in EPL_TEAMS], validators=[DataRequired()])
    #match_datetime = DateTimeField('Match Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')


class CreateMatchWeekForm(FlaskForm):
    # Don't import models at module level - do it in the route instead
    week_number = SelectField('Week Number', validators=[DataRequired()])
    season = SelectField('Season', validators=[DataRequired()])
    predictions_open_time = DateTimeField('Predictions Open Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    predictions_close_time = DateTimeField('Predictions Close Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    fixtures = FieldList(FormField(FixtureForm), min_entries=1, max_entries=20)
    submit = SubmitField('Create Match Week')


class PredictionForm(FlaskForm):
    home_score = IntegerField('Home Score', validators=[DataRequired(), NumberRange(min=0, max=20)])
    away_score = IntegerField('Away Score', validators=[DataRequired(), NumberRange(min=0, max=20)])


class CreateSeasonForm(FlaskForm):
    start_year = IntegerField('Start Year', validators=[DataRequired()])
    end_year = IntegerField('End Year', validators=[DataRequired()])
    submit = SubmitField('Submit')