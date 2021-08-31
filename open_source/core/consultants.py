import hashlib
import bcrypt
import base64
from random import choice, randint

from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class Consultant(db.Base):
    __tablename__ = 'consultants'

    STATE_ARCHIVED = 3
    STATE_PENDING = 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    consultant_id = Column(Integer, primary_key=True)
    state = Column(Integer, default=1)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    email = Column(String(length=50))
    temp_password = Column(String(length=50))
    password = Column(String(length=50))
    branch = Column(String(length=50))
    number = Column(String(length=50))
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.parlour_id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    def to_dict(self):
        return {
            'id': self.consultant_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'state': self.state,
            'branch': self.branch,
            'number': self.number,
            "modified": self.modified_at,
            'created': self.created_at,
            'parlour': self.parlour.to_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.consultant_id,
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
        session.commit()

    @staticmethod
    def to_password_hash(plaintext):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plaintext, salt)

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
            session.query(Consultant).filter(func.trim(Consultant.username) ==
                                       username.strip(), Consultant.state == Consultant.STATE_ACTIVE).one()
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False

    @classmethod
    def is_email_unique(cls, session, username):
        try:
            session.query(Consultant).filter(func.trim(Consultant.email) ==
                                       username.strip(), Consultant.state == Consultant.STATE_ACTIVE).one()
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False
    
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