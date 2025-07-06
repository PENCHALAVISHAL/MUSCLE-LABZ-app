from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from config import config
from .models import db, User, UserData, ExerciseLibrary, Workout, HydrationTracking, WeightTracking, BodyFatTracking
from datetime import datetime, timedelta
import json
from sqlalchemy.sql import func
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression

# Initialize Flask extensions
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app

app = create_app()

# Routes
@app.route('/')
def index():
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'error')
            return redirect(url_for('register'))

        # Check if user or email already exists
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash('Username or email already exists. Please choose another.', 'error')
            return redirect(url_for('register'))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            # Check if user_data exists
            if user.user_data:
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login successful! Please complete your basic info.', 'success')
                return redirect(url_for('basic_info'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/basic_info', methods=['GET', 'POST'])
@login_required
def basic_info():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        height = request.form.get('height')
        weight = request.form.get('weight')
        body_fat = request.form.get('body_fat')
        gender = request.form.get('gender')
        activity_level = request.form.get('activity_level')
        fitness_goal = request.form.get('fitness_goal')
        if not all([name, age, height, weight, gender, activity_level, fitness_goal]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('basic_info'))
        try:
            # Convert body_fat to float if provided
            body_fat = float(body_fat) if body_fat else None
            # Check if user_data exists
            user_data = current_user.user_data
            if user_data:
                # Update existing data
                user_data.name = name
                user_data.age = int(age)
                user_data.height = float(height)
                user_data.weight = float(weight)
                user_data.body_fat = body_fat
                user_data.gender = gender
                user_data.activity_level = activity_level
                user_data.fitness_goal = fitness_goal
                user_data.updated_at = datetime.utcnow()
            else:
                # Create new user_data
                user_data = UserData(
                    user_id=current_user.id,
                    name=name,
                    age=int(age),
                    height=float(height),
                    weight=float(weight),
                    body_fat=body_fat,
                    gender=gender,
                    activity_level=activity_level,
                    fitness_goal=fitness_goal
                )
                db.session.add(user_data)
            db.session.commit()
            flash('Your details have been saved!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Please enter valid numbers for age, height, weight, and body fat.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your data. Please try again.', 'error')
    # GET request - show form with existing data
    user_data = current_user.user_data
    return render_template('basic_info.html', user_data=user_data)

@app.route('/dashboard')
@login_required
def dashboard():
    user_data = current_user.user_data
    
    if not user_data:
        # Only redirect to basic_info if user_data does not exist
        flash('Please complete your basic information first.', 'info')
        return redirect(url_for('basic_info'))
    
    return render_template('dashboard.html', user_data=user_data)

@app.route('/workout_tracker')
@login_required
def workout_tracker():
    categories_from_db = db.session.query(ExerciseLibrary.category).distinct().order_by(ExerciseLibrary.category).all()
    categories = [c[0] for c in categories_from_db]
    return render_template('workout.html', categories=categories, user_data=current_user.user_data)

@app.route('/api/exercises')
@login_required
def api_exercises():
    category = request.args.get('category')
    if not category:
        return jsonify([])
    exercises = ExerciseLibrary.query.filter_by(category=category).order_by(ExerciseLibrary.name).all()
    return jsonify([{'name': ex.name} for ex in exercises])

@app.route('/save_workout', methods=['POST'])
@login_required
def save_workout():
    if request.method == 'POST':
        exercise = request.form.get('exercise')
        weight = request.form.get('weight')
        reps = request.form.get('reps')
        sets = request.form.get('sets')
        notes = request.form.get('notes')
        unit = request.form.get('unit')

        if not all([exercise, weight, reps, sets]):
            flash('Please fill in all required fields.', category='error')
            return redirect(url_for('workout_tracker'))

        try:
            weight_val = float(weight)
            if unit == 'lbs':
                weight_val = weight_val * 0.453592  # Convert to kg
            
            new_workout = Workout(
                user_id=current_user.id,
                exercise=exercise,
                weight=round(weight_val, 2),
                reps=int(reps),
                sets=int(sets),
                notes=notes
            )
            db.session.add(new_workout)
            db.session.commit()
            flash('Workout logged successfully!', category='success')
        except ValueError:
            flash('Please enter valid numbers for weight, reps, and sets.', category='error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', category='error')
            db.session.rollback()
        
        return redirect(url_for('workout_tracker'))

@app.route('/workouts/view')
@login_required
def view_workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()

    # Analytics data
    analytics_data = db.session.query(
        Workout.exercise,
        func.sum(Workout.weight * Workout.reps * Workout.sets).label('total_weight')
    ).filter_by(user_id=current_user.id).group_by(Workout.exercise).order_by(func.sum(Workout.weight * Workout.reps * Workout.sets).desc()).limit(10).all()

    chart_labels = [data[0] for data in analytics_data]
    chart_values = [data[1] for data in analytics_data]

    return render_template('view_workouts.html', workouts=workouts, chart_labels=chart_labels, chart_values=chart_values, user_data=current_user.user_data)

@app.route('/analytics')
@login_required
def analytics():
    user_id = current_user.id
    # 1. Daily Training Volume by Exercise
    daily_volume = db.session.query(
        Workout.date,
        Workout.exercise,
        func.sum(Workout.weight * Workout.reps * Workout.sets).label('volume')
    ).filter_by(user_id=user_id).group_by(Workout.date, Workout.exercise).order_by(Workout.date).all()
    # Format for JS: {date: {exercise: volume}}
    stacked_data = defaultdict(dict)
    exercises_set = set()
    for d, ex, v in daily_volume:
        stacked_data[str(d)][ex] = float(v)
        exercises_set.add(ex)
    stacked_dates = sorted(stacked_data.keys())
    stacked_exercises = sorted(exercises_set)
    stacked_volumes = []
    for date in stacked_dates:
        row = []
        for ex in stacked_exercises:
            row.append(stacked_data[date].get(ex, 0))
        stacked_volumes.append(row)
    # 2. Most Frequent Exercises (top 6)
    freq_ex = db.session.query(
        Workout.exercise,
        func.count(Workout.id)
    ).filter_by(user_id=user_id).group_by(Workout.exercise).order_by(func.count(Workout.id).desc()).limit(6).all()
    freq_labels = [x[0] for x in freq_ex]
    freq_counts = [x[1] for x in freq_ex]
    # 3. Average Reps per Exercise (top 6)
    avg_reps = db.session.query(
        Workout.exercise,
        func.avg(Workout.reps)
    ).filter_by(user_id=user_id).group_by(Workout.exercise).order_by(func.avg(Workout.reps).desc()).limit(6).all()
    avg_reps_labels = [x[0] for x in avg_reps]
    avg_reps_values = [round(x[1], 2) for x in avg_reps]
    # 4. Workout Category Distribution (pie)
    pie_data = db.session.query(
        ExerciseLibrary.category,
        func.count(Workout.id)
    ).join(ExerciseLibrary, Workout.exercise == ExerciseLibrary.name)
    pie_data = pie_data.filter(Workout.user_id == user_id)
    pie_data = pie_data.group_by(ExerciseLibrary.category).all()
    pie_labels = [x[0] for x in pie_data]
    pie_counts = [x[1] for x in pie_data]
    return render_template('analytics.html',
        stacked_dates=stacked_dates,
        stacked_exercises=stacked_exercises,
        stacked_volumes=stacked_volumes,
        freq_labels=freq_labels,
        freq_counts=freq_counts,
        avg_reps_labels=avg_reps_labels,
        avg_reps_values=avg_reps_values,
        pie_labels=pie_labels,
        pie_counts=pie_counts,
        user_data=current_user.user_data
    )

@app.route('/delete_workouts', methods=['POST'])
@login_required
def delete_workouts():
    ids = request.form.getlist('workout_ids')
    if ids:
        Workout.query.filter(Workout.id.in_(ids), Workout.user_id==current_user.id).delete(synchronize_session=False)
        db.session.commit()
        flash(f"Deleted {len(ids)} workout(s).", 'success')
    else:
        flash('No workouts selected for deletion.', 'error')
    return redirect(url_for('view_workouts'))

@app.route('/hydration', methods=['GET'])
@login_required
def hydration():
    user = current_user
    # Get most recent weight entry
    latest_weight_entry = WeightTracking.query.filter_by(user_id=user.id).order_by(WeightTracking.date.desc()).first()
    weight = latest_weight_entry.weight if latest_weight_entry else (user.user_data.weight if user.user_data and user.user_data.weight else None)
    goal_obj = user.hydration_goal
    if goal_obj:
        hydration_goal = int(goal_obj.daily_goal)
    elif weight:
        hydration_goal = int(float(weight) * 35)
    else:
        hydration_goal = 2000
    # Only get today's hydration logs
    today = datetime.utcnow().date()
    logs = db.session.query(HydrationTracking).filter_by(user_id=user.id, date=today).order_by(HydrationTracking.id.asc()).all()
    hydration_logs = [{'amount': log.amount, 'date': log.date.strftime('%Y-%m-%d'), 'id': log.id} for log in logs]
    today_total = sum(log.amount for log in logs)
    return render_template('hydration.html', weight=weight if weight else '--', hydration_goal=hydration_goal, hydration_logs=hydration_logs, today_total=today_total, user_data=user.user_data)

@app.route('/hydration/view')
@login_required
def view_hydration():
    user = current_user
    logs = db.session.query(HydrationTracking).filter_by(user_id=user.id).order_by(HydrationTracking.date.desc(), HydrationTracking.id.desc()).all()
    hydration_logs = [{'amount': log.amount, 'date': log.date.strftime('%Y-%m-%d'), 'id': log.id} for log in logs]
    return render_template('view_hydration.html', hydration_logs=hydration_logs, user_data=user.user_data)

@app.route('/log_hydration', methods=['POST'])
@login_required
def log_hydration():
    user = current_user
    data = request.get_json()
    amount = data.get('amount')
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400
    today = datetime.utcnow().date()
    entry = HydrationTracking(user_id=user.id, amount=amount_val, date=today)
    db.session.add(entry)
    db.session.commit()
    today_total = db.session.query(db.func.sum(HydrationTracking.amount)).filter_by(user_id=user.id, date=today).scalar() or 0
    # Hydration goal logic
    latest_weight_entry = WeightTracking.query.filter_by(user_id=user.id).order_by(WeightTracking.date.desc()).first()
    weight = latest_weight_entry.weight if latest_weight_entry else (user.user_data.weight if user.user_data and user.user_data.weight else None)
    goal_obj = user.hydration_goal
    if goal_obj:
        hydration_goal = int(goal_obj.daily_goal)
    elif weight:
        hydration_goal = int(float(weight) * 35)
    else:
        hydration_goal = 2000
    return jsonify({'today_total': today_total, 'hydration_goal': hydration_goal})

@app.route('/weight', methods=['GET', 'POST'])
@login_required
def weight():
    user = current_user
    message = None
    today = datetime.utcnow().date()
    if request.method == 'POST':
        if 'set_goal' in request.form:
            goal_weight_val = request.form.get('goal_weight')
            if goal_weight_val:
                try:
                    goal_weight_val = float(goal_weight_val)
                    if goal_weight_val > 0:
                        if user.user_data:
                            user.user_data.goal_weight = goal_weight_val
                            db.session.commit()
                            message = 'Goal weight updated.'
                except (ValueError, TypeError):
                    message = 'Please enter a valid goal weight.'
        elif 'save_weight' in request.form:
            weight_val = request.form.get('weight')
            try:
                weight_val = float(weight_val)
                if weight_val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                message = 'Please enter a valid weight.'
            else:
                entry = WeightTracking.query.filter_by(user_id=user.id, date=today).first()
                if entry:
                    entry.weight = weight_val
                else:
                    entry = WeightTracking(user_id=user.id, weight=weight_val, date=today)
                    db.session.add(entry)
                db.session.commit()
                message = 'Weight saved successfully.'
    # Get all weight logs for chart
    logs = WeightTracking.query.filter_by(user_id=user.id).order_by(WeightTracking.date.asc()).all()
    weight_logs = [{'date': w.date.strftime('%Y-%m-%d'), 'weight': float(w.weight)} for w in logs]
    regression = []
    estimated_date = None
    goal_weight = user.user_data.goal_weight if user.user_data and user.user_data.goal_weight else None
    if len(weight_logs) >= 2 and goal_weight:
        dates = [w['date'] for w in weight_logs]
        weights = [w['weight'] for w in weight_logs]
        base_date = datetime.strptime(dates[0], '%Y-%m-%d')
        days = np.array([(datetime.strptime(d, '%Y-%m-%d') - base_date).days for d in dates]).reshape(-1, 1)
        model = LinearRegression().fit(days, weights)
        regression = model.predict(days).tolist()
        slope = model.coef_[0]
        intercept = model.intercept_
        if slope != 0:
            x_target = (goal_weight - intercept) / slope
            if x_target >= days[-1]:
                target_date = base_date + timedelta(days=int(x_target))
                estimated_date = target_date.strftime('%Y-%m-%d')
    return render_template('weight.html', weight_logs=weight_logs, message=message, today=today.strftime('%Y-%m-%d'), user_data=user.user_data, regression=regression, estimated_date=estimated_date, goal_weight=goal_weight)

@app.route('/weight/view')
@login_required
def view_weight():
    user = current_user
    logs = WeightTracking.query.filter_by(user_id=user.id).order_by(WeightTracking.date.desc()).all()
    weight_logs = [{'id': w.id, 'date': w.date.strftime('%Y-%m-%d'), 'weight': float(w.weight)} for w in logs]
    return render_template('view_weight.html', weight_logs=weight_logs, user_data=user.user_data)

@app.route('/delete_weight_entries', methods=['POST'])
@login_required
def delete_weight_entries():
    user = current_user
    ids = request.form.getlist('weight_ids')
    if ids:
        WeightTracking.query.filter(WeightTracking.id.in_(ids), WeightTracking.user_id==user.id).delete(synchronize_session=False)
        db.session.commit()
    return redirect(url_for('view_weight'))

@app.route('/delete_hydration_entries', methods=['POST'])
@login_required
def delete_hydration_entries():
    user = current_user
    ids = request.form.getlist('hydration_ids')
    if ids:
        HydrationTracking.query.filter(HydrationTracking.user_id==user.id, HydrationTracking.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
    return redirect(url_for('view_hydration'))

@app.route('/bodyfat', methods=['GET', 'POST'])
@login_required
def bodyfat():
    user = current_user
    user_data = user.user_data
    gender = user_data.gender if user_data and user_data.gender else 'Male'
    age = user_data.age if user_data and user_data.age else 25
    height = user_data.height if user_data and user_data.height else 170
    message = None
    suggestion = None
    chart_data = []
    goal_body_fat = user_data.goal_body_fat if user_data and hasattr(user_data, 'goal_body_fat') and user_data.goal_body_fat else None
    if request.method == 'POST':
        if 'set_goal' in request.form:
            goal_body_fat_val = request.form.get('goal_body_fat')
            try:
                goal_body_fat_val = float(goal_body_fat_val)
                if goal_body_fat_val > 0:
                    user_data.goal_body_fat = goal_body_fat_val
                    # Only create a new BodyFatTracking entry if the latest entry's goal is different
                    latest_entry = db.session.query(BodyFatTracking).filter_by(user_id=user.id).order_by(BodyFatTracking.date.desc(), BodyFatTracking.id.desc()).first()
                    if not latest_entry or latest_entry.goal_body_fat != goal_body_fat_val:
                        entry = BodyFatTracking(user_id=user.id, date=datetime.utcnow().date(), goal_body_fat=goal_body_fat_val)
                        db.session.add(entry)
                    db.session.commit()
                    message = 'Goal body fat updated.'
                    goal_body_fat = goal_body_fat_val
                else:
                    message = 'Please enter a valid goal body fat percentage.'
            except Exception:
                message = 'Please enter a valid goal body fat percentage.'
        else:
            try:
                waist = float(request.form.get('waist'))
                neck = float(request.form.get('neck'))
                hip = float(request.form.get('hip')) if gender.lower() == 'female' else 0
                if gender.lower() == 'male':
                    body_fat = 495 / (1.0324 - 0.19077 * np.log10(waist - neck) + 0.15456 * np.log10(height)) - 450
                else:
                    body_fat = 495 / (1.29579 - 0.35004 * np.log10(waist + hip - neck) + 0.22100 * np.log10(height)) - 450
                body_fat = round(body_fat, 2)
                # Always create a new entry (do not update existing entry for today)
                entry = BodyFatTracking(user_id=user.id, date=datetime.utcnow().date(), body_fat=body_fat, waist_circumference=waist, neck_circumference=neck, hip_circumference=hip, goal_body_fat=goal_body_fat)
                print(f"NEW BODYFAT ENTRY: user_id={user.id}, date={entry.date}, body_fat={body_fat}, waist={waist}, neck={neck}, hip={hip}, goal_body_fat={goal_body_fat}")
                db.session.add(entry)
                db.session.commit()
                message = f'Body Fat % recorded: {body_fat}%'
                # Suggestion
                if body_fat < 10:
                    suggestion = "Your body fat is very low. Ensure you're not compromising hormonal or joint health."
                elif 10 <= body_fat <= 18:
                    suggestion = "Excellent! You're in the athletic range. Maintain your training & nutrition consistency."
                elif 18 < body_fat <= 24:
                    suggestion = "You're in a healthy range. Consider gradual reduction if aiming for more definition."
                elif 24 < body_fat <= 30:
                    suggestion = "Moderate fat level. Incorporate more movement & monitor intake."
                else:
                    suggestion = "Consider creating a structured plan to gradually reduce fat. Focus on strength & consistency."
            except Exception as e:
                message = f'Calculation error: {e}'
    # Always reload user_data to get the latest goal_body_fat
    user_data = user.user_data
    goal_body_fat = user_data.goal_body_fat if user_data and hasattr(user_data, 'goal_body_fat') and user_data.goal_body_fat is not None else None
    # Load chart data
    logs = db.session.query(BodyFatTracking).filter_by(user_id=user.id).order_by(BodyFatTracking.date.asc()).all()
    chart_data = [{'date': log.date.strftime('%Y-%m-%d'), 'body_fat': log.body_fat} for log in logs]

    # Linear regression and estimated goal date
    regression = []
    estimated_date = None
    if len(chart_data) >= 2 and goal_body_fat:
        dates = [row['date'] for row in chart_data if row['body_fat'] is not None]
        values = [row['body_fat'] for row in chart_data if row['body_fat'] is not None]
        if len(dates) >= 2:
            base_date = datetime.strptime(dates[0], '%Y-%m-%d')
            days = np.array([(datetime.strptime(d, '%Y-%m-%d') - base_date).days for d in dates]).reshape(-1, 1)
            model = LinearRegression().fit(days, values)
            regression = model.predict(days).tolist()
            slope = model.coef_[0]
            intercept = model.intercept_
            if slope != 0:
                x_target = (goal_body_fat - intercept) / slope
                MAX_ESTIMATE_DAYS = 3650  # 10 years
                try:
                    days = int(x_target)
                    if days < 0:
                        estimated_date = None  # Already reached or impossible
                    elif days > MAX_ESTIMATE_DAYS:
                        estimated_date = "unrealistic"  # Too far in the future
                    else:
                        target_date = base_date + timedelta(days=days)
                        estimated_date = target_date.strftime('%Y-%m-%d')
                except (ValueError, OverflowError):
                    estimated_date = None

    return render_template('bodyfat.html', gender=gender, age=age, height=height, message=message, suggestion=suggestion, chart_data=chart_data, user_data=user_data, goal_body_fat=goal_body_fat, regression=regression, estimated_date=estimated_date)

@app.route('/bodyfat/view')
@login_required
def view_bodyfat():
    user = current_user
    user_data = user.user_data  # Ensure latest user_data is loaded
    logs = BodyFatTracking.query.filter_by(user_id=user.id).order_by(BodyFatTracking.date.asc()).all()
    bodyfat_logs = []
    goal_history = []
    last_goal = None
    for log in logs:
        entry = {
            'id': log.id,
            'date': log.date.strftime('%Y-%m-%d'),
            'body_fat': float(log.body_fat) if log.body_fat is not None else None,
            'goal_body_fat': float(log.goal_body_fat) if log.goal_body_fat is not None else None,
            'waist': log.waist_circumference,
            'neck': log.neck_circumference,
            'hip': log.hip_circumference
        }
        bodyfat_logs.append(entry)
        # Build goal history: add a row only when the goal changes
        if log.goal_body_fat is not None and log.goal_body_fat != last_goal:
            goal_history.append({'date': log.date.strftime('%Y-%m-%d'), 'value': log.goal_body_fat})
            last_goal = log.goal_body_fat
    # Pass the current goal separately
    current_goal = user_data.goal_body_fat if user_data and user_data.goal_body_fat is not None else None
    return render_template('view_bodyfat.html', bodyfat_logs=bodyfat_logs, user_data=user_data, current_goal=current_goal, goal_history=goal_history)

@app.route('/delete_bodyfat_entries', methods=['POST'])
@login_required
def delete_bodyfat_entries():
    user = current_user
    ids = request.form.getlist('bodyfat_ids')
    if ids:
        BodyFatTracking.query.filter(BodyFatTracking.id.in_(ids), BodyFatTracking.user_id==user.id).delete(synchronize_session=False)
        db.session.commit()
    return redirect(url_for('view_bodyfat'))

@app.route('/suggestions')
@login_required
def suggestions():
    user = current_user
    user_data = user.user_data

    # --- Curated suggestion lists ---
    workout_tips = [
        "Gradually increase training volume (weight × reps × sets).",
        "Track personal records and aim to beat them every 2–3 weeks.",
        "Start light and build steadily for long-term gains.",
        "Don't increase weight if form is breaking — add reps first.",
        "Add one rep per set before adding weight.",
        "Use rest-pause or tempo to challenge muscles.",
        "Push the last set close to failure weekly.",
        "Vary rep ranges (6–12) across weeks for muscle confusion.",
        "Use double progression: reps first, then weight.",
        "Apply overload to isolation exercises too.",
        "Keep track of total weekly volume per muscle group.",
        "Increase time under tension instead of weight sometimes.",
        "Overload doesn't always mean heavier — try slower reps.",
        "Do more sets or sessions if recovery allows.",
        "Include overload for core movements like planks (duration).",
        "Use drop sets occasionally to push volume.",
        "Focus on effort, not just numbers.",
        "Use feedback loops from soreness or fatigue wisely.",
        "Take deloads every 6–8 weeks to reload progress.",
        "Progress isn't linear — zoom out over months."
    ]
    hydration_tips = [
        "Stay hydrated — aim for 3L water daily.",
        "Electrolytes help during sweaty high-volume days.",
        "Don't skip meals — consistency helps recovery.",
        "Hydration affects muscle cramping and recovery.",
        "Hydration supports joint health and pump.",
        "Refuel after intense sessions — don't wait too long.",
        "Log your hydration to notice what works best.",
        "Active rest days help circulation and mood.",
        "Hydration is key for performance and recovery."
    ]
    weight_tips = [
        "Track morning fasted weight for consistency.",
        "Weekly averages are more accurate than daily.",
        "Gaining? Aim for 0.25–0.5 kg/week to avoid fat gain.",
        "Losing? 0.5–1% of bodyweight/week is safe.",
        "Don't panic over short-term scale spikes.",
        "Use trendlines, not day-to-day shifts.",
        "Weigh yourself 3–5x/week minimum for trend data.",
        "Drastic drops = water or glycogen loss, not fat.",
        "Muscle weighs more per volume — check visuals.",
        "Track weight with energy, sleep, and mood notes.",
        "Plateaus are normal — review intake/activity.",
        "Overfeeding for 1 day won't ruin a bulk/cut.",
        "Increase food slowly during bulks — avoid bloat.",
        "Bulking? Add cardio to keep heart health up.",
        "Cutting? Strength train to maintain lean mass.",
        "Record milestones (e.g., reached 70kg) to stay inspired.",
        "Hydration and food volume affect daily changes.",
        "Weight is a tool — not a verdict.",
        "Progress = stronger, leaner, more consistent — not just lighter.",
        "Use visual comparisons every 4 weeks."
    ]
    bodyfat_tips = [
        "Track body fat % monthly for meaningful change.",
        "Focus on fat loss, not just weight loss.",
        "Preserve muscle with strength training in deficits.",
        "Avoid rapid cuts — slow loss retains lean mass.",
        "Visual check-ins (photos) help more than just numbers.",
        "Combine strength + cardio for efficient fat loss.",
        "Sleep is critical — poor rest disrupts fat metabolism.",
        "Track waist size as fat loss indicator.",
        "Consistency in diet matters more than extremes.",
        "Progress may stall — adjust calories if needed.",
        "High protein keeps you full and protects muscle.",
        "Fat loss plateaus? Add NEAT (walking, movement).",
        "Don't judge progress weekly — think 4–6 weeks.",
        "Accept fluctuations — hydration, food, and hormones affect scale.",
        'Avoid "dirty cutting" — you\'ll lose muscle fast.',
        "Stick to evidence-based fat loss, not fads.",
        "Diet breaks can help when stalled.",
        "Body recomposition is slower, but sustainable.",
        "Measure from the same state (morning, fasted).",
        "Increased strength at same weight = leaner body."
    ]

    # --- Workouts ---
    workout_logs = sorted(user.workouts, key=lambda x: x.date, reverse=True) if hasattr(user, 'workouts') else []
    workout_suggestions = []
    if workout_logs:
        total_sessions = len(workout_logs)
        if total_sessions < 2:
            workout_suggestions.append("Try to log at least 2 workouts per week for steady progress.")
        else:
            workout_suggestions.append(f"Great job! You've logged {total_sessions} workouts. Keep up the consistency.")
        # Example: check for progressive overload
        if total_sessions >= 2:
            last = workout_logs[0]
            prev = workout_logs[1]
            if hasattr(last, 'total_volume') and hasattr(prev, 'total_volume'):
                if last.total_volume > prev.total_volume:
                    workout_suggestions.append("You're increasing your training volume. This is key for muscle growth!")
                else:
                    workout_suggestions.append("Try to gradually increase your training volume (weight × reps × sets) over time.")
        # Add 3-5 motivational tips
        workout_suggestions += workout_tips[:5]
    else:
        workout_suggestions.append("No workouts logged yet. Start your first session to get personalized tips!")
        workout_suggestions += workout_tips[:5]

    # --- Hydration ---
    hydration_logs = sorted(user.hydration_tracking, key=lambda x: x.date, reverse=True) if hasattr(user, 'hydration_tracking') else []
    hydration_suggestions = []
    if hydration_logs:
        avg_water = sum([h.amount for h in hydration_logs if h.amount]) / len(hydration_logs)
        if avg_water < 2000:
            hydration_suggestions.append("Try to drink at least 2L of water daily for optimal hydration.")
        else:
            hydration_suggestions.append("Great hydration habits! Keep maintaining your water intake.")
        hydration_suggestions += hydration_tips[:4]
    else:
        hydration_suggestions.append("No hydration logs yet. Track your water intake for better performance.")
        hydration_suggestions += hydration_tips[:4]

    # --- Weight ---
    weight_logs = sorted(user.weight_tracking, key=lambda x: x.date, reverse=True) if hasattr(user, 'weight_tracking') else []
    weight_suggestions = []
    if weight_logs:
        weights = [w.weight for w in weight_logs if w.weight]
        if len(weights) >= 2:
            delta = weights[0] - weights[-1]
            if abs(delta) < 0.5:
                weight_suggestions.append("Your weight is stable. If you have a goal, consider adjusting your nutrition or activity.")
            elif delta > 0:
                weight_suggestions.append("You're losing weight. Make sure it's at a healthy rate (0.5-1% per week).")
            else:
                weight_suggestions.append("You're gaining weight. If bulking, aim for 0.25-0.5 kg/week.")
        else:
            weight_suggestions.append("Log more weight entries to see trends and get tailored advice.")
        weight_suggestions += weight_tips[:5]
    else:
        weight_suggestions.append("No weight entries yet. Start tracking to get feedback on your progress.")
        weight_suggestions += weight_tips[:5]

    # --- Body Fat ---
    bodyfat_logs = sorted(user.body_fat_tracking, key=lambda x: x.date, reverse=True) if hasattr(user, 'body_fat_tracking') else []
    bodyfat_suggestions = []
    if bodyfat_logs:
        bodyfats = [b.body_fat for b in bodyfat_logs if b.body_fat]
        if len(bodyfats) >= 2:
            delta = bodyfats[0] - bodyfats[-1]
            if abs(delta) < 0.5:
                bodyfat_suggestions.append("Body fat % is stable. For fat loss, review your calorie intake and activity.")
            elif delta > 0:
                bodyfat_suggestions.append("Body fat % is decreasing. Great job! Maintain your routine for continued progress.")
            else:
                bodyfat_suggestions.append("Body fat % is increasing. Review your nutrition and training plan.")
        else:
            bodyfat_suggestions.append("Log more body fat entries to get personalized suggestions.")
        bodyfat_suggestions += bodyfat_tips[:5]
    else:
        bodyfat_suggestions.append("No body fat entries yet. Track your body fat % for more insights.")
        bodyfat_suggestions += bodyfat_tips[:5]

    return render_template('suggestions.html',
        workout_suggestions=workout_suggestions,
        hydration_suggestions=hydration_suggestions,
        weight_suggestions=weight_suggestions,
        bodyfat_suggestions=bodyfat_suggestions,
        user_data=user.user_data
    )

# Database initialization
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

@app.cli.command('reset-db')
def reset_db():
    """Drop all tables and create them again."""
    db.drop_all()
    db.create_all()
    print('Database has been reset.')

@app.cli.command('populate-exercises')
def populate_exercises():
    """Populate the exercise library."""
    exercise_data = [
        # Chest
        ("Barbell Bench Press", "Chest", "Pectorals", "Compound chest press"),
        ("Incline Bench Press", "Chest", "Upper Pectorals", "Targets upper chest"),
        ("Dumbbell Chest Press", "Chest", "Pectorals", "Dumbbell chest press"),
        ("Chest Fly (Machine)", "Chest", "Pectorals", "Isolation chest exercise"),
        ("Chest Fly (Dumbbell)", "Chest", "Pectorals", "Isolation chest exercise"),
        ("Push-Ups", "Chest", "Pectorals", "Bodyweight chest exercise"),
        ("Cable Crossover", "Chest", "Pectorals", "Isolation chest exercise"),
        
        # Back
        ("Pull-Ups", "Back", "Lats", "Compound back exercise"),
        ("Chin-Ups", "Back", "Lats / Biceps", "Compound back exercise"),
        ("Lat Pulldown", "Back", "Lats", "Machine back exercise"),
        ("Barbell Bent-Over Row", "Back", "Lats / Rhomboids", "Compound back exercise"),
        ("Dumbbell Rows", "Back", "Lats", "Unilateral back exercise"),
        ("T-Bar Row", "Back", "Lats", "Machine back exercise"),
        ("Seated Cable Row", "Back", "Lats / Rhomboids", "Machine back exercise"),
        ("Deadlifts", "Back", "Full Body", "Compound lifting exercise"),
        
        # Shoulders
        ("Overhead Press (Barbell)", "Shoulders", "Deltoids", "Compound shoulder exercise"),
        ("Overhead Press (Dumbbell)", "Shoulders", "Deltoids", "Compound shoulder exercise"),
        ("Lateral Raises", "Shoulders", "Lateral Deltoids", "Isolation shoulder exercise"),
        ("Front Raises", "Shoulders", "Anterior Deltoids", "Isolation shoulder exercise"),
        ("Rear Delt Fly", "Shoulders", "Posterior Deltoids", "Isolation shoulder exercise"),
        ("Arnold Press", "Shoulders", "Deltoids", "Compound shoulder exercise"),
        ("Upright Rows", "Shoulders", "Deltoids / Traps", "Compound shoulder exercise"),
        
        # Biceps
        ("Barbell Curl", "Biceps", "Biceps", "Isolation bicep exercise"),
        ("Dumbbell Curl", "Biceps", "Biceps", "Isolation bicep exercise"),
        ("Preacher Curl", "Biceps", "Biceps", "Isolation bicep exercise"),
        ("Concentration Curl", "Biceps", "Biceps", "Isolation bicep exercise"),
        ("Cable Bicep Curl", "Biceps", "Biceps", "Isolation bicep exercise"),
        
        # Triceps
        ("Tricep Pushdown", "Triceps", "Triceps", "Isolation tricep exercise"),
        ("Dips", "Triceps", "Triceps", "Bodyweight tricep exercise"),
        ("Overhead Tricep Extension", "Triceps", "Triceps", "Isolation tricep exercise"),
        ("Skull Crushers", "Triceps", "Triceps", "Isolation tricep exercise"),
        ("Close-Grip Bench Press", "Triceps", "Triceps / Chest", "Compound tricep exercise"),
        
        # Arms (Forearms)
        ("Wrist Curls", "Arms", "Forearms", "Isolation forearm exercise"),
        ("Reverse Curls", "Arms", "Forearms / Biceps", "Isolation forearm exercise"),
        ("Farmer's Walk", "Arms", "Forearms / Grip", "Grip strength exercise"),
        
        # Legs
        ("Squats (Barbell)", "Legs", "Quads / Glutes", "Compound leg exercise"),
        ("Squats (Bodyweight)", "Legs", "Quads / Glutes", "Bodyweight leg exercise"),
        ("Leg Press", "Legs", "Quads", "Machine leg exercise"),
        ("Lunges", "Legs", "Quads / Glutes", "Unilateral leg exercise"),
        ("Leg Extension", "Legs", "Quadriceps", "Isolation leg exercise"),
        ("Romanian Deadlift", "Legs", "Hamstrings / Glutes", "Compound leg exercise"),
        ("Leg Curl", "Legs", "Hamstrings", "Isolation leg exercise"),
        ("Glute-Ham Raise", "Legs", "Hamstrings / Glutes", "Posterior chain exercise"),
        ("Hip Thrusts", "Legs", "Glutes", "Isolation glute exercise"),
        ("Glute Bridges", "Legs", "Glutes", "Bodyweight glute exercise"),
        ("Cable Kickbacks", "Legs", "Glutes", "Isolation glute exercise"),
        ("Standing Calf Raise", "Legs", "Calves", "Isolation calf exercise"),
        ("Seated Calf Raise", "Legs", "Calves", "Isolation calf exercise"),
        ("Donkey Calf Raise", "Legs", "Calves", "Isolation calf exercise"),
        
        # Core & Abs
        ("Planks", "Core & Abs", "Core", "Isometric core exercise"),
        ("Crunches", "Core & Abs", "Abs", "Isolation ab exercise"),
        ("Hanging Leg Raises", "Core & Abs", "Lower Abs", "Advanced ab exercise"),
        ("Russian Twists", "Core & Abs", "Obliques", "Rotational core exercise"),
        ("Cable Woodchoppers", "Core & Abs", "Obliques", "Rotational core exercise"),
        ("Ab Rollouts", "Core & Abs", "Core", "Advanced core exercise"),
    ]
    
    for name, category, muscle_group, description in exercise_data:
        exercise = ExerciseLibrary.query.filter_by(name=name).first()
        if not exercise:
            exercise = ExerciseLibrary(
                name=name,
                category=category,
                muscle_group=muscle_group,
                description=description
            )
            db.session.add(exercise)
    
    db.session.commit()
    print('Exercise library populated!')

if __name__ == '__main__':
    app.run(debug=True, port=8080) 