from random import choice, randint
import base64
import hashlib
from xmlrpc.client import boolean

from open_source import config
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from open_source.core.roles import Role

class User(db.Base):
    __tablename__ = 'users'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    first_name = Column(String(length=30))
    last_name = Column(String(length=30))
    number = Column(String(length=200))
    branch = Column(String(length=200))
    state = Column(Integer, default=1)
    email = Column(String(length=255))
    username = Column(String(length=255))
    password = Column(String(length=255))
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def main_members(cls):
        return relationship("MainMember", back_populates="user")

    @declared_attr
    def role_id(cls):
        return Column(Integer, ForeignKey('roles.id'))

    @declared_attr
    def role(cls):
        return relationship('Role')

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'state': self.state,
            "branch": self.branch,
            'username': self.username,
            "modified": self.modified_at,
            'created': self.created_at,
            "parlour": self.parlour.to_dict()
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
    
    @property
    def is_consultant(self):
        return self.role_id == Role.IS_CONSULTANT

    @property
    def is_admin(self):
        return self.role_id == Role.IS_ADMIN

    @property
    def is_parlour(self):
        return self.role_id == Role.IS_PARLOUR

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
    def is_username_unique(cls, session, username) -> boolean:
        try:
            user = session.query(User).filter(func.trim(User.username) ==
                                       username.strip(), User.state == User.STATE_ACTIVE).one()
            if user:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False

    @classmethod
    def is_email_unique(cls, session, email) -> boolean:
        try:
            user = session.query(User).filter(
                func.trim(User.email) == email.strip(),
                User.state == User.STATE_ACTIVE
            ).one()
            if user:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
        return False
