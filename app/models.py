from app import db
import sqlalchemy.orm as so
import sqlalchemy as sa
from datetime import datetime, date, timezone

# Message model
class SupportMessage(db.Model):
    # primary key
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # course name
    course_name: so.Mapped[str] = so.mapped_column(sa.String(256), index=True, nullable=False)
    # message title
    message_title: so.Mapped[str] = so.mapped_column(sa.String(256), index=True, nullable=False)
    # message content (long text)
    message_content: so.Mapped[str] = so.mapped_column(sa.String(500), index=True, nullable=False)
    # priority（1-10）
    priority: so.Mapped[int] = so.mapped_column(sa.Integer, index=True, nullable=False, default=5)
    # teacher email
    teacher_email: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, unique=False, index=True)
    # publish date (Only date, no time)
    publish_date: so.Mapped[date] = so.mapped_column(sa.Date, nullable=False, default=date.today)
    # deadline (Only date, no time)
    deadline: so.Mapped[date] = so.mapped_column(sa.Date, nullable=False, default=date.today)


    def __repr__(self):
        return f'<SupportMessage {self.id} - {self.message_title} ({self.course_name})>'