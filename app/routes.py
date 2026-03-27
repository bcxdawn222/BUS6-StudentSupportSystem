import os
import uuid
import logging
from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, current_app, json
from werkzeug.utils import secure_filename, send_from_directory

from app import app
from app import db
from app.models import SupportMessage, SurveyResponse, User, Homework, Appointment
from app.forms import (SupportMessageForm, TeacherUpload, SurveyForm,
                       RegistrationForm, LoginForm, HomeworkForm, AppointmentForm)
from sqlalchemy import func, cast, Float
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_login import login_user, current_user, logout_user, login_required

logger = logging.getLogger(__name__)

# Register
@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check for duplicate username or email
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists. Please choose another.", "danger")
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please use another.", "danger")
            return render_template('register.html', form=form)
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash("Registration failed. Username or email already in use.", "danger")
    return render_template('register.html', form=form)

# Login
@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        flash("Login failed. Please check your email and password.", "danger")
    return render_template('login.html', form=form)

# Logout
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

# Home page: submit and display all messages
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SupportMessageForm()

    if form.validate_on_submit():
        #Only teachers could create message
        if current_user.role != "teacher":
            flash("Only teachers can post messages", "danger")
            return redirect(url_for('index'))
        try:
            # Create a support message record
            support_msg = SupportMessage(
                user_id=current_user.id,
                course_name=form.course_name.data.strip(),
                message_title=form.message_title.data.strip(),
                message_content=form.message_content.data.strip(),
                priority=form.priority.data,
                teacher_email=form.teacher_email.data.strip().lower(),
                publish_date=form.publish_date.data,
                deadline=form.deadline.data
            )

            db.session.add(support_msg)
            db.session.commit()
            flash(f"Support message '{form.message_title.data}' added successfully!", "success")
            return redirect(url_for('index'))

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback transaction on error
            flash(f"Error adding message: {str(e)}", "danger")

    # ========== Added: Query Survey statistics (pass to homepage template) ==========
    survey_total = SurveyResponse.query.count()  # Total survey submissions
    survey_avg = None
    try:
        # Fixed: Explicitly convert string to Float (replace original cast method)
        avg_quality = db.session.query(
            func.avg(cast(SurveyResponse.teaching_quality, Float))
        ).scalar()
        survey_avg = round(avg_quality, 1) if avg_quality else 0
    except Exception as e:
        logger.warning("Failed to compute survey average: %s", e)
        survey_avg = 0
    # ========== End of addition ==========

    # Display all messages in descending order of publication date
    support_messages = SupportMessage.query.order_by(SupportMessage.publish_date.desc()).all()

    # ========== Modified: Pass survey_total/survey_avg to template ==========
    return render_template(
        'index.html',
        current_user=current_user,
        form=form,
        student_infos=support_messages,
        survey_total=survey_total,  # Added
        survey_avg=survey_avg       # Added
    )


# List page: Display all messages in descending order of priority
@app.route('/listing')
@login_required
def listing_messages():
    # In descending order of priority (with high priority first)
    messages = SupportMessage.query.order_by(SupportMessage.priority.desc()).all()
    logger.info("Number of messages retrieved: %d", len(messages))
    return render_template('listing.html', students=messages)


# Search page: Search for messages by teacher email
@app.route('/searching')
@login_required
def search_messages():
    email = request.args.get("email", "").strip().lower()
    course_name = request.args.get("course_name", "").strip().lower()
    message_title = request.args.get("message_title", "").strip().lower()
    query = SupportMessage.query

    # Fuzzy search conditions
    if email:
        query = query.filter(SupportMessage.teacher_email.ilike(f"%{email}%"))
    if course_name:
        query = query.filter(SupportMessage.course_name.ilike(f"%{course_name}%"))
    if message_title:
        query = query.filter(SupportMessage.message_title.ilike(f"%{message_title}%"))

    results = query.order_by(SupportMessage.priority.desc()).all()

    # Filter high-priority messages (≥8)
    high_priority = query.filter(SupportMessage.priority >= 8).all()

    return render_template(
        'searching.html',
        results=results,
        high=high_priority,
        email=email,
        course_name=course_name,
        message_title=message_title
    )


# Advanced search: by priority/ranking/average score (priority)
@app.route('/more_searching')
@login_required
def more_search():
    query = SupportMessage.query
    # Filter by priority (high/medium/low)
    priority_level = request.args.get("priority", "")

    sort_by = request.args.get("sort", "")

    # Priority filtering option
    if priority_level == 'high':
        query = query.filter(SupportMessage.priority >= 8)
    elif priority_level == 'medium':
        query = query.filter(SupportMessage.priority.between(4, 7))
    elif priority_level == 'low':
        query = query.filter(SupportMessage.priority <= 3)

    # Sorting option
    if sort_by == "priority_high":
        query = query.order_by(SupportMessage.priority.desc())
    elif sort_by == "priority_low":
        query = query.order_by(SupportMessage.priority.asc())
    elif sort_by == "newest":
        query = query.order_by(SupportMessage.publish_date.desc())

    results = query.all()

    # Calculate average priority
    try:
        avg_priority = db.session.query(func.avg(SupportMessage.priority)).scalar()
        avg_priority_final = round(avg_priority, 0) if avg_priority else 0
    except Exception as e:
        logger.warning("Failed to compute avg priority: %s", e)
        avg_priority_final = 0

    return render_template(
        'further_search.html',
        results=results,
        status=priority_level,
        order=sort_by,
        results1_final=avg_priority_final
    )


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def file_upload():
    #Only teachers can upload
    if current_user.role != "teacher":
        flash("Only teachers can upload files", "danger")
        return redirect(url_for('index'))
    # Create an object for upload form
    form = TeacherUpload()
    filename = None
    # Create path for json file to store upload records
    file_path = os.path.join(
        current_app.root_path, 'static', 'uploads.json')
    try:
        with open(file_path, "r") as file:
            feedback_store = json.load(file)
    except FileNotFoundError:
        feedback_store = []

    # Save upload data to json file
    if form.validate_on_submit():
        # Get uploaded file and save to uploads directory FIRST
        uploaded_file = form.file.data
        saved_filename = None
        if uploaded_file:
            raw_name = secure_filename(uploaded_file.filename)
            if not raw_name:
                raw_name = 'unnamed_file'
            name, ext = os.path.splitext(raw_name)
            saved_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
            uploaded_folder = current_app.config['UPLOAD_FOLDER']
            uploaded_file.save(os.path.join(uploaded_folder, saved_filename))
        # Now save metadata with correct filename
        upload_data = {
            "teacher_name": form.teacher_name.data,
            "course_name": form.course_name.data,
            "remark": form.remark.data,
            "filename": saved_filename,
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        feedback_store.append(upload_data)
        with open(file_path, "w") as f:
            json.dump(feedback_store, f, indent=4)
        flash("File uploaded successfully!", "success")
        return redirect(url_for("file_upload", filename=saved_filename))
    # List all files (exclude .gitkeep) for downloading
    uploaded_folder = current_app.config['UPLOAD_FOLDER']
    files = [f for f in os.listdir(uploaded_folder) if f != ".gitkeep"]
    # Get filename from request args for download
    filename = request.args.get('filename')
    # Render template for form, uploads and downloads
    return render_template("upload.html", form=form, filename=filename, files=files)


"""
Clicking the Download link triggers a GET request with the filename in the URL. 
Flask passes this filename to the download_file route, which returns the file to the browser as a download.
"""


@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    uploaded_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(
        uploaded_folder,
        filename,
        as_attachment=True)


# Choose a file to download from uploaded files list
@app.route('/downloads')
@login_required
def downloads():
    uploaded_folder = current_app.config['UPLOAD_FOLDER']
    # List all files (exclude .gitkeep) and sort in reverse order
    files = [f for f in os.listdir(uploaded_folder) if f != ".gitkeep"]
    files.sort(reverse=True)
    return render_template('downloads.html', files=files)


@app.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    form = SurveyForm()

    if form.validate_on_submit():
        try:
            # Create survey record (reuse SupportMessage data processing logic)
            survey_record = SurveyResponse(
                grade=form.grade.data.strip(),
                gender=form.gender.data.strip(),
                teaching_quality=form.teaching_quality.data.strip(),
                feedback=form.feedback.data.strip() if form.feedback.data else ""
            )

            db.session.add(survey_record)
            db.session.commit()
            # Flash message (consistent style with existing features: success/danger)
            flash("Teaching quality survey submitted successfully! Thank you for your feedback.", "success")
            return redirect(url_for('index'))  # Redirect to homepage after submission

        except SQLAlchemyError as e:
            db.session.rollback()  # Reuse existing error rollback logic
            flash(f"Failed to submit survey: {str(e)}", "danger")

    # Render survey page for GET requests
    return render_template('survey.html', title='Teaching Quality Survey', form=form)


# Optional: Survey results page (backend feature, reuse more_search statistics logic)
@app.route('/survey_results')
@login_required
def survey_results():
    # Query all survey responses (sorted by submission time descending)
    survey_responses = SurveyResponse.query.order_by(SurveyResponse.submitted_at.desc()).all()

    # Statistics data (reuse func.avg/func.count logic from more_search)
    try:
        # Total survey submissions
        total_surveys = SurveyResponse.query.count()
        # Submission count by grade
        grade_stats = db.session.query(
            SurveyResponse.grade,
            func.count(SurveyResponse.id)
        ).group_by(SurveyResponse.grade).all()
        # ========== Modified: Explicitly convert string to Float (fix average calculation) ==========
        avg_quality = db.session.query(
            func.avg(cast(SurveyResponse.teaching_quality, Float))
        ).scalar()
        avg_quality_final = round(avg_quality, 1) if avg_quality else 0
    except Exception as e:
        total_surveys = 0
        grade_stats = []
        avg_quality_final = 0
        flash(f"Error loading survey results: {str(e)}", "danger")

    return render_template(
        'survey_results.html',
        responses=survey_responses,
        total=total_surveys,
        grade_stats=grade_stats,
        avg_quality=avg_quality_final
    )


# Submit Homework page
@app.route('/submit_homework', methods=['GET', 'POST'])
@login_required
def submit_homework():
    form = HomeworkForm()
    if form.validate_on_submit():
        saved_filename = ""
        uploaded_file = form.file.data
        if uploaded_file:
            raw_name = secure_filename(uploaded_file.filename)
            if not raw_name:
                raw_name = 'unnamed_file'
            name, ext = os.path.splitext(raw_name)
            saved_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
            uploaded_folder = current_app.config['UPLOAD_FOLDER']
            uploaded_file.save(os.path.join(uploaded_folder, saved_filename))
        try:
            hw = Homework(
                user_id=current_user.id,
                course_name=form.course_name.data.strip(),
                title=form.title.data.strip(),
                description=form.description.data.strip() if form.description.data else "",
                filename=saved_filename
            )
            db.session.add(hw)
            db.session.commit()
            flash("Homework submitted successfully!", "success")
            return redirect(url_for('submit_homework'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Error submitting homework: {str(e)}", "danger")
    # Show student's own submissions
    my_homeworks = Homework.query.filter_by(user_id=current_user.id).order_by(Homework.submitted_at.desc()).all()
    return render_template('submit_homework.html', form=form, homeworks=my_homeworks)


# Book Appointment page
@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        try:
            appt = Appointment(
                user_id=current_user.id,
                teacher_name=form.teacher_name.data.strip(),
                subject=form.subject.data.strip(),
                appointment_date=form.appointment_date.data,
                time_slot=form.time_slot.data,
                notes=form.notes.data.strip() if form.notes.data else ""
            )
            db.session.add(appt)
            db.session.commit()
            flash("Appointment booked successfully!", "success")
            return redirect(url_for('book_appointment'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Error booking appointment: {str(e)}", "danger")
    # Show student's own appointments
    my_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.created_at.desc()).all()
    return render_template('book_appointment.html', form=form, appointments=my_appointments)


# Delete message (teacher can only delete own messages)
@app.route('/delete_message/<int:msg_id>', methods=['POST'])
@login_required
def delete_message(msg_id):
    msg = SupportMessage.query.get_or_404(msg_id)
    if msg.user_id != current_user.id:
        flash("You can only delete your own messages.", "danger")
        return redirect(url_for('index'))
    try:
        db.session.delete(msg)
        db.session.commit()
        flash("Message deleted successfully.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Error deleting message: {str(e)}", "danger")
    return redirect(url_for('index'))


# Custom error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500