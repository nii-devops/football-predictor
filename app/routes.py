from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from .models import db, User, Season, MatchWeek, Fixture, Prediction, Week
from .forms import FixtureForm, CreateMatchWeekForm, PredictionForm, CreateSeasonForm
from wtforms import FieldList, FormField
from . import oauth
import os

bp = Blueprint('main', __name__)

ADMIN_EMAILS = os.getenv('ADMIN_EMAILS')

weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 
        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]

# Sky Sports API Integration (Mock implementation - replace with actual API)
def fetch_fixtures_from_sky_sports():
    mock_fixtures = [
        {
            'home_team': 'Manchester United',
            'away_team': 'Arsenal',
            'match_datetime': datetime.now() + timedelta(days=7),
        },
        {
            'home_team': 'Chelsea',
            'away_team': 'Liverpool',
            'match_datetime': datetime.now() + timedelta(days=7, hours=2),
        }
    ]
    return mock_fixtures

@bp.route('/')
def index():
    active_match_weeks = MatchWeek.query.filter_by(is_active=True).all()
    return render_template('index.html', active_match_weeks=active_match_weeks)


@bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('login.html')


# The following routes require OAuth and app context, which will be handled in __init__.py
# Placeholders for now:
@bp.route('/authorize/google')
def google_auth():
    redirect_uri = url_for('main.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route('/authorize/google/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        user = User.query.filter_by(google_id=user_info['sub']).first()
        if not user:
            user = User.query.filter_by(email=user_info['email']).first()
            if user:
                user.google_id = user_info['sub']
                user.name = user_info['name']
            else:
                if user_info['email'] in ADMIN_EMAILS:
                    user = User(
                    google_id=user_info['sub'],
                    email=user_info['email'],
                    name=user_info['name'],
                    is_admin=True
                    )
                    db.session.add(user)
                else:
                    user = User(
                        google_id=user_info['sub'],
                        email=user_info['email'],
                        name=user_info['name']
                    )
                    db.session.add(user)
            db.session.commit()
        login_user(user)
        flash('Successfully logged in!', 'success')
        return redirect(url_for('main.index'))
    flash('Authentication failed', 'error')
    return redirect(url_for('main.login'))



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))


@bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    return render_template('admin/dashboard.html')


@bp.route('/admin/test_route')
@login_required
def test_route():
    print("=== TEST ROUTE CALLED ===")
    return "Test route works!"


@bp.route('/admin/create_match_week', methods=['GET', 'POST'])
@login_required
def create_match_week():
    print("=== CREATE MATCH WEEK ROUTE CALLED ===")
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Test database connection
    try:
        weeks = Week.query.order_by(Week.id).all()
        print(f"Found {len(weeks)} weeks in database")
        seasons = Season.query.order_by(Season.season_start_year.asc()).all()
        print(f"Found {len(seasons)} seasons in database")
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
    week_choices = [(week.id, f"Week {week.week_number}") for week in weeks]
    season_choices = [(season.id, f"{season.season_start_year}-{season.season_end_year}") for season in seasons]

    # Initialize form with POST data if this is a POST request
    if request.method == 'POST':
        # Count the number of fixtures in the POST data
        num_fixtures = len([key for key in request.form if key.startswith('fixtures-') and key.endswith('-home_team')])
        print(f"Number of fixtures detected in POST data: {num_fixtures}")
        
        # Create a new form class with the correct number of entries
        if num_fixtures > 0:
            # Create a dynamic form class with the right number of entries
            class DynamicCreateMatchWeekForm(CreateMatchWeekForm):
                fixtures = FieldList(FormField(FixtureForm), min_entries=num_fixtures, max_entries=20)
            
            form = DynamicCreateMatchWeekForm(request.form)
        else:
            form = CreateMatchWeekForm(request.form)
    else:
        form = CreateMatchWeekForm()
    
    form.season.choices = season_choices
    form.week_number.choices = week_choices

    print(f"Request method: {request.method}")
    print(f"Form is submitted: {form.is_submitted()}")
    print(f"Form validation: {form.validate()}")
    print(f"Form data: {request.form}")
    print(f"Number of fixtures in form: {len(form.fixtures)}")
    if not form.validate():
        print(f"Form errors: {form.errors}")
        for field_name, errors in form.errors.items():
            print(f"Field {field_name} errors: {errors}")

    if form.validate_on_submit():
        print("=== FORM VALIDATION PASSED ===")
        # Print form data for debugging
        print(f'Week number data: {form.week_number.data}')
        print(f'Season data: {form.season.data}')
        print(f'Predictions open time: {form.predictions_open_time.data}')
        print(f'Predictions close time: {form.predictions_close_time.data}')
        print(f'Number of fixtures: {len(form.fixtures)}')
        
        for i, fixture_form in enumerate(form.fixtures):
            print(f'Processing fixture {i}: home_team={fixture_form.home_team.data}, away_team={fixture_form.away_team.data}')
            if fixture_form.home_team.data and fixture_form.away_team.data:
                print(f'Fixture {i+1}: {fixture_form.home_team.data} vs {fixture_form.away_team.data}')
        
        try:
            match_week = MatchWeek(
                week_id=form.week_number.data,
                season_id=form.season.data,
                predictions_open_time=form.predictions_open_time.data,
                predictions_close_time=form.predictions_close_time.data
            )
            
            print(f'Creating MatchWeek: week_id={form.week_number.data}, season_id={form.season.data}')
            db.session.add(match_week)
            db.session.flush()  # This gets us the match_week.id
            print(f'MatchWeek created with ID: {match_week.id}')
            
            fixture_count = 0
            for fixture_form in form.fixtures:
                if fixture_form.home_team.data and fixture_form.away_team.data:
                    fixture = Fixture(
                        match_week_id=match_week.id,
                        home_team=fixture_form.home_team.data,
                        away_team=fixture_form.away_team.data,
                    )
                    db.session.add(fixture)
                    fixture_count += 1
                    print(f'Added fixture: {fixture_form.home_team.data} vs {fixture_form.away_team.data}')
            
            db.session.commit()
            print(f'Successfully committed {fixture_count} fixtures to database')
            flash(f'Match Week created successfully with {fixture_count} fixtures!', 'success')
            return redirect(url_for('main.admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f'Error creating match week: {str(e)}')
            flash(f'Error creating match week: {str(e)}', 'error')
            return redirect(url_for('main.admin_dashboard'))
    else:
        print("=== FORM VALIDATION FAILED ===")
    return render_template('admin/create_match_week.html', form=form)


@bp.route('/admin/import_fixtures', methods=['POST'])
@login_required
def import_fixtures():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    try:
        fixtures = fetch_fixtures_from_sky_sports()
        flash(f'Imported {len(fixtures)} fixtures successfully!', 'success')
        return jsonify({'success': True, 'count': len(fixtures)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/create_season', methods=['GET','POST'])
@login_required
def create_season():

    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # seasons = Season.query.order_by(Season.season_start_year.asc()).all()
    # season_choices = [(season.id, f"{season.season_start_year}/{season.season_end_year}") for season in seasons]
    form = CreateSeasonForm()
    # form.season.choices = season_choices

    if form.validate_on_submit():
        start = form.start_year.data
        end = form.end_year.data

        if Season.query.filter_by(season_start_year=start, season_end_year=end).first():
            flash('Season exists', 'warning')
            return redirect(request.referrer)
        
        else:
            try:
                db.session.add(
                    Season(
                        season_start_year=start,
                        season_end_year=end
                    )
                )
                db.session.commit()
                return redirect(url_for('main.index'))
            except Exception as e:
                #error = jsonify({'error': str(e)}), 500
                flash(f'Error: {e}', 'danger')
    return render_template('admin/create_season.html', form=form)


@bp.route('/admin/activate_match_week/<int:week_id>', methods=['POST'])
@login_required
def activate_match_week(week_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    MatchWeek.query.update({MatchWeek.is_active: False})
    match_week = MatchWeek.query.get_or_404(week_id)
    match_week.is_active = True
    db.session.commit()
    flash(f'Match Week {match_week.week_number} activated!', 'success')
    return redirect(url_for('main.admin_dashboard'))




@bp.route('/predict/<int:week_id>')
@login_required
def predict_match_week(week_id):
    match_week = MatchWeek.query.get_or_404(week_id)
    if not match_week.is_predictions_open:
        flash('Predictions are not open for this match week.', 'warning')
        return redirect(url_for('main.index'))
    fixtures = match_week.fixtures
    user_predictions = {}
    for fixture in fixtures:
        prediction = Prediction.query.filter_by(user_id=current_user.id, fixture_id=fixture.id).first()
        if prediction:
            user_predictions[fixture.id] = prediction
    return render_template('predict.html', match_week=match_week, fixtures=fixtures, user_predictions=user_predictions)



@bp.route('/submit_prediction/<int:fixture_id>', methods=['POST'])
@login_required
def submit_prediction(fixture_id):
    fixture = Fixture.query.get_or_404(fixture_id)
    if not fixture.match_week.is_predictions_open:
        return jsonify({'error': 'Predictions are closed for this fixture'}), 400
    home_score = int(request.form['home_score'])
    away_score = int(request.form['away_score'])
    prediction = Prediction.query.filter_by(user_id=current_user.id, fixture_id=fixture_id).first()
    if prediction:
        prediction.home_score_prediction = home_score
        prediction.away_score_prediction = away_score
        prediction.updated_at = datetime.utcnow()
    else:
        prediction = Prediction(
            user_id=current_user.id,
            fixture_id=fixture_id,
            home_score_prediction=home_score,
            away_score_prediction=away_score
        )
        db.session.add(prediction)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/leaderboard')
@login_required
def leaderboard():
    user_points = db.session.query(
        User.name,
        db.func.sum(Prediction.points_earned).label('total_points')
    ).join(Prediction).group_by(User.id).order_by(db.desc('total_points')).all()
    return render_template('leaderboard.html', user_points=user_points)


@bp.route('/api/add_fixture_form')
def add_fixture_form():
    form = FixtureForm()
    return render_template('admin/_fixture_form.html', form=form, index='__INDEX__')






