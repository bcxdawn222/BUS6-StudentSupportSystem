from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, IntegerField, TextAreaField, SelectField, RadioField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange, EqualTo
from flask_wtf.file import FileField, FileAllowed


# Support Message Submission Form (Core business form)
class SupportMessageForm(FlaskForm):

    course_name = StringField(
        "Course Name",
        validators=[
            DataRequired(message="Course name is required"),
            Length(max=256, message="Course name cannot exceed 256 characters")
        ]
    )

    message_title = StringField(
        "Message Title",
        validators=[
            DataRequired(message="Message title is required"),
            Length(max=256, message="Title cannot exceed 256 characters")
        ]
    )

    message_content = TextAreaField(
        "Message Content",
        validators=[
            DataRequired(message="Message content is required"),
            Length(max=500, message="Content cannot exceed 500 characters")
        ]
    )

    # Priority level (1-10, default value = 5)
    priority = IntegerField(
        "Priority (1-10)",
        validators=[
            DataRequired(message="Priority is required"),
            NumberRange(min=1, max=10, message="Priority must be between 1 and 10")
        ],
        default=5
    )

    teacher_email = StringField(
        "Teacher Email",
        validators=[
            DataRequired(message="Teacher email is required"),
            Email(message="Please enter a valid email address")
        ]
    )

    # Publish date (default value = current date)
    publish_date = DateField(
        "Publish Date",
        format="%Y-%m-%d",
        default=date.today,
        validators=[DataRequired(message="Publish date is required")]
    )

    # Deadline date (default value = current date)
    deadline = DateField(
        "Deadline",
        format="%Y-%m-%d",
        default=date.today,
        validators=[DataRequired(message="Deadline is required")]
    )

    submit = SubmitField("Submit Support Message")


# Teacher File Upload Form
class TeacherUpload(FlaskForm):

    teacher_name = StringField(
        "Your Full Name",
        validators=[DataRequired()]
    )

    course_name = StringField(
        "Course Name",
        validators=[DataRequired()]
    )

    remark = TextAreaField(
        "Remark (optional)",
        validators=[Length(max=150)]
    )

    file = FileField(
        "Upload File (PDF, DOCX, ZIP, JPG, PNG)",
        validators=[
            DataRequired(),
            FileAllowed(['pdf', 'docx', 'doc', 'jpg', 'png', 'zip', 'txt'], "Only documents allowed")
        ]
    )

    submit = SubmitField("Upload File")

class SurveyForm(FlaskForm):
    # Grade selection dropdown (consistent with existing field naming/validation style)
    grade = SelectField(
        "Your Grade",
        choices=[
            ("", "Please select your grade"),  # Placeholder prompt
            ("Junior 1", "Junior 1"),
            ("Junior 2", "Junior 2"),
            ("Junior 3", "Junior 3"),
            ("Senior 1", "Senior 1"),
            ("Senior 2", "Senior 2"),
            ("Senior 3", "Senior 3")
        ],
        validators=[
            DataRequired(message="Grade is required")  # Validation message consistent with existing style
        ]
    )

    # Gender selection (radio buttons)
    gender = RadioField(
        "Your Gender",
        choices=[("Male", "Male"), ("Female", "Female")],
        validators=[
            DataRequired(message="Gender is required")
        ]
    )

    # Teaching satisfaction rating dropdown
    teaching_quality = SelectField(
        "Teaching Satisfaction Rating",
        choices=[
            ("", "Please rate teaching quality"),
            ("5", "5 - Very Satisfied"),
            ("4", "4 - Satisfied"),
            ("3", "3 - Average"),
            ("2", "2 - Dissatisfied"),
            ("1", "1 - Very Dissatisfied")
        ],
        validators=[
            DataRequired(message="Teaching satisfaction rating is required")
        ]
    )

    # Additional feedback (optional, consistent with TeacherUpload's remark style)
    feedback = TextAreaField(
        "Additional Feedback (optional)",
        validators=[
            Length(max=1000, message="Feedback cannot exceed 1000 characters")
        ],
        render_kw={"placeholder": "Enter your suggestions or comments here"}
    )

    # Submit button (consistent naming style with existing buttons)
    submit = SubmitField("Submit Survey")

#Registration
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    role = SelectField(
        "Role",
        choices=[("student", "Student"), ("teacher", "Teacher")],
        validators=[DataRequired()]
    )

    submit = SubmitField('Register')

#  Login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# Homework Submission Form (Student)
class HomeworkForm(FlaskForm):
    course_name = StringField(
        "Course Name",
        validators=[DataRequired(message="Course name is required"), Length(max=256)]
    )
    title = StringField(
        "Homework Title",
        validators=[DataRequired(message="Title is required"), Length(max=256)]
    )
    description = TextAreaField(
        "Description (optional)",
        validators=[Length(max=1000)]
    )
    file = FileField(
        "Attachment (PDF, DOCX, ZIP, JPG, PNG)",
        validators=[
            FileAllowed(['pdf', 'docx', 'doc', 'jpg', 'png', 'zip', 'txt'], "Only documents allowed")
        ]
    )
    submit = SubmitField("Submit Homework")


# Appointment Booking Form (Student)
class AppointmentForm(FlaskForm):
    teacher_name = StringField(
        "Teacher Name",
        validators=[DataRequired(message="Teacher name is required"), Length(max=128)]
    )
    subject = StringField(
        "Subject / Reason",
        validators=[DataRequired(message="Subject is required"), Length(max=256)]
    )
    appointment_date = DateField(
        "Preferred Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Date is required")]
    )
    time_slot = SelectField(
        "Preferred Time Slot",
        choices=[
            ("", "Please select a time slot"),
            ("09:00-10:00", "09:00 - 10:00"),
            ("10:00-11:00", "10:00 - 11:00"),
            ("11:00-12:00", "11:00 - 12:00"),
            ("13:00-14:00", "13:00 - 14:00"),
            ("14:00-15:00", "14:00 - 15:00"),
            ("15:00-16:00", "15:00 - 16:00"),
            ("16:00-17:00", "16:00 - 17:00"),
        ],
        validators=[DataRequired(message="Time slot is required")]
    )
    notes = TextAreaField(
        "Additional Notes (optional)",
        validators=[Length(max=500)]
    )
    submit = SubmitField("Book Appointment")