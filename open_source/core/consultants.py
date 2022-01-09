import hashlib
import base64
from open_source import config
from random import choice, randint

from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Consultant(db.Base):
    __tablename__ = 'consultants'

    STATE_ARCHIVED = 3
    STATE_PENDING = 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    state_to_text = {
        STATE_ARCHIVED: 'Archived',
        STATE_PENDING: 'Pending',
        STATE_ACTIVE: 'Active',
        STATE_DELETED: 'Deleted'
    }

    id = Column(Integer, primary_key=True)
    state = Column(Integer, default=1)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    email = Column(String(length=50))
    username = Column(String(length=50))
    temp_password = Column(String(length=50))
    password = Column(String(length=50))
    branch = Column(String(length=50))
    number = Column(String(length=50))
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    @declared_attr
    def applicants(cls):
        return relationship("Applicant", back_populates="consultant")

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'username': self.username,
            'state': self.state,
            'branch': self.branch,
            'number': self.number,
            "modified": self.modified_at,
            'created': self.created_at,
            'parlour': self.parlour.to_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'branch': self.branch,
            'number': self.number
        }

    def save(self, session):
        session.add(self)
        session.commit()

    def is_deleted(self) -> bool:
        return self.state == self.STATE_DELETED

    def make_deleted(self):
        self.state = self.STATE_DELETED

    def delete(self, session):
        self.make_deleted()
        self.on_delete_clean_up()
        session.commit()

    def on_delete_clean_up(self):
        for a in self.applicants:
            a.make_deleted()

    @property
    def pretty_name(self) -> str:
        return '{} {}'.format(self.first_name, self.last_name)

    @staticmethod
    def to_password_hash(plaintext):
        salt = config.get_config().password_salt
        return hashlib.sha1((salt + plaintext).encode('utf-8')).hexdigest()

    def set_password(self, plaintext):
        self.password = self.to_password_hash(plaintext)

    def authenticate(self, password):
        return self.password == self.to_password_hash(password)

    @staticmethod
    def generate_password():

        c = 'bcdfghjklmnprstvwz'
        v = 'aeiou'

        def chars():
            return choice(c) + choice(v) + choice(c + v)

        return chars() + chars() + str(randint(10, 99))

    def to_webtoken_payload(self):
        return {'id': self.id}

    @classmethod
    def is_username_unique(cls, session, username):
        try:
            consultant = session.query(Consultant).filter(func.trim(Consultant.username) ==
                                       username.strip(), Consultant.state == Consultant.STATE_ACTIVE).one()
            if consultant:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False

    @classmethod
    def is_email_unique(cls, session, email):
        try:
            consultant = session.query(Consultant).filter(
                func.trim(Consultant.email) == email.strip(),
                Consultant.state == Consultant.STATE_ACTIVE
            ).one()
            if consultant:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False
    
    def send_signup_email(self):
        sender_email = "nkosanani21test@@gmail.com"
        receiver_email = "nkosanan@citiqprepaid.co.za"
        # password = input("Type your password and press enter:")

        message = MIMEMultipart("alternative")
        message["Subject"] = "multipart test"
        message["From"] = sender_email
        message["To"] = receiver_email

        html = """\
        <html>
        <body>
            <p>Hi,<br>
            You are receiving this email because you are a consultant for {parlour}.<br>
            Your temporary password is: {temp_password}
            Click on the link to go to the main website where you can login
            <a href="http:/localhost:4200">{parlour}</a> 
            has many great tutorials.
            </p>
        </body>
        </html>
        """.format(parlour=self.parlour.parlourname, temp_password=self.temp_password)

        # Turn these into plain/html MIMEText objects
        part = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            # server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )

    @classmethod
    def new_consultant(cls, request):
        return Consultant(
            first_name=request["first_name"],
            last_name=request["last_name"],
            email=request["email"],
            state=Consultant.STATE_ACTIVE,
            branch=request["branch"],
            number=request["number"],
            modified=request["modified_at"],
            created=request["created_at"],
            parlour_id=request["parlour_id"]
        )