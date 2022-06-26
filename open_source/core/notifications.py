import datetime

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from open_source import config, db, utils

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Time
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from open_source.core.main_members import MainMember
from open_source.core.payments import Payment
from open_source.core.invoices import Invoice

from open_source.core.resources import DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE
from open_source.core.roles import Role
from open_source.core.users import User

conf = config.get_config()


class Notification(db.Base):
    STATE_DELETED = 0
    STATE_ACTIVE = 1

    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)

    recipients = Column(Text)

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    consultants = Column(Text)
    week_days = Column(String(length=200))
    state = Column(Integer, default=1)
    scheduled_time = Column(Time)
    modified_at = Column(DateTime)
    last_run_date = Column(DateTime)
    created_at = Column(DateTime)

    def save(self, session):
        session.add(self)
        session.commit()

    def is_deleted(self) -> bool:
        return self.state == self.STATE_DELETED

    def make_deleted(self):
        self.state = self.STATE_DELETED

    def delete(self, session):
        self.make_deleted()
        session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "week_days": self.week_days,
            "scheduled_time": self.scheduled_time,
            "consultants": self.consultants,
            "recipients": self.recipients,
            "parlour": self.parlour.to_dict()
        }

    @staticmethod
    def get_money_collected(session, user):
        main_members = session.query(MainMember).filter(MainMember.user_id == user.id, MainMember.state == MainMember.STATE_ACTIVE).all()
        main_member_ids = [main_member.id for main_member in main_members]

        payments =  session.query(Payment).filter(Payment.main_member_id.in_(main_member_ids), Payment.created >= datetime.datetime.today().date()).all()

        if len(payments) > 0:
            payment_ids = [payment.id for payment in payments]
            invoices =  session.query(Invoice).filter(Invoice.payment_id.in_(payment_ids), Invoice.state == Invoice.STATE_ACTIVE).all()
            return sum([invoice.amount for invoice in invoices])
        return 0

    def send_email(self, session, parlour):
        port = 465  # For SSL
        smtp_server = "mail.osource.co.za"
        sender_email = conf.SENDER_EMAIL
        password = conf.SENDER_PASSWORD
        to_list = [x.strip() for x in self.recipients.split(",")]

        message = MIMEMultipart("alternative")
        message["Subject"] = "Daily Financial Report"
        message["From"] = sender_email

        consultants = []
        sum = 0

        for id in self.consultants.split(", "):
            user = session.query(User).filter(User.id == int(id), User.state == User.STATE_ACTIVE, User.role_id == Role.IS_CONSULTANT).first()
            amount = self.get_money_collected(session, user)

            entry = """
            <tr>
                <td>{} {}</td>
                <td>R{}</td>
            </tr>""".format(user.first_name, user.last_name, amount)

            consultants.append(entry)
            sum += amount

        html = {"html": """
            {}
            <tr>
                <td></td>
            </tr>
            <tr>
                <td><strong>{}</strong></td>
                <td><strong>R{}</strong></td>
            </tr>
            """.format(''.join(consultants), parlour.parlourname, sum)}

        email_body = utils.render_template(
            DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE,
            html
        )

        # Turn these into plain/html MIMEText objects
        # part1 = MIMEText(text, "plain")
        part2 = MIMEText(email_body, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        # message.attach(part1)
        message.attach(part2)
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_list, message.as_string())
