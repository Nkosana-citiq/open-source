from random import choice, randint
import base64
import hashlib

from open_source import config
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class Admin(db.Base):
    __tablename__ = 'admin'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    first_name = Column(String(length=30))
    last_name = Column(String(length=30))
    number = Column(String(length=200))
    state = Column(Integer, default=1)
    email = Column(String(length=255))
    username = Column(String(length=255))
    password = Column(String(length=255))
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'state': self.state,
            'username': self.username,
            "modified": self.modified_at,
            'created': self.created_at
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
            session.query(Admin).filter(func.trim(Admin.username) ==
                                       username.strip(), Admin.state == Admin.STATE_ACTIVE).one()
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False

    @classmethod
    def is_email_unique(cls, session, email):
        try:
            session.query(Admin).filter(
                func.trim(Admin.email) == email.strip(),
                Admin.state == Admin.STATE_ACTIVE
            ).one()
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False
