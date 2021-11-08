from random import choice, randint

import hashlib
import datetime

from sqlalchemy.sql.sqltypes import Boolean

from open_source import config
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound



class PasswordReset(db.Base):
    STATE_DELETED = 0
    STATE_ACTIVE = 1

    __tablename__ = 'password_resets'

    id = Column(Integer, primary_key=True)

    code = Column(String(255))

    user_id = Column(Integer, ForeignKey('parlours.id'))
    user = relationship('Parlour')

    email = Column(String(length=255), default='')

    state = Column(Integer, default=1)

    expired = Column(DateTime)
    modified = Column(DateTime)
    created = Column(DateTime)

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


class Parlour(db.Base):
    __tablename__ = 'parlours'

    STATE_ARCHIVED = 3
    STATE_PENDING = 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    parlourname = Column(String(length=200))
    personname = Column(String(length=200))
    number = Column(String(length=200))
    state = Column(Integer, default=1)
    email = Column(String(length=255))
    username = Column(String(length=255))
    address = Column(String(length=255))
    password = Column(String(length=255))
    number_of_sms = Column(Integer())
    agreed_to_terms = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def plans(cls):
        return relationship("Plan", back_populates="parlour")

    @declared_attr
    def consultants(cls):
        return relationship("Consultant", back_populates="parlour")

    @declared_attr
    def main_members(cls):
        return relationship("MainMember", back_populates="parlour")

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'email': self.email,
            'parlour_name': self.parlourname,
            'person_name': self.personname,
            'state': self.state,
            'username': self.username,
            'address': self.address,
            'number_of_sms': self.number_of_sms,
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
        self.on_delete_clean_up()
        session.commit()

    def on_delete_clean_up(self):
        for c in self.consultants:
            c.make_deleted()
        for p in self.plans:
            p.make_deleted()
        for m in self.main_members:
            m.make_deleted()

    @property
    def pretty_name(self) -> str:
        return self.personname.title()

    @staticmethod
    def to_password_hash(plaintext):
        salt = config.get_config().password_salt
        return hashlib.sha1((salt + plaintext).encode('utf-8')).hexdigest()

    def set_password(self, plaintext):
        self.password = self.to_password_hash(plaintext)

    def authenticate(self, password):
        return self.password == self.to_password_hash(password)

    @classmethod
    def get_password_reset(session, email):
        try:
            return session.query(Parlour)\
                .filter(
                    Parlour.email == email
                ).one()

        except MultipleResultsFound:
            return None
        except NoResultFound:
            return None
        return None

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
            parlour = session.query(Parlour).filter(func.trim(Parlour.username) ==
                                       username.strip(), Parlour.state == Parlour.STATE_ACTIVE).one()
            if parlour:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True

    @classmethod
    def is_email_unique(cls, session, email):
        try:
            parlour = session.query(Parlour).filter(
                func.trim(Parlour.email) == email.strip(),
                Parlour.state == Parlour.STATE_ACTIVE
            ).one()
            if parlour:
                return False
        except MultipleResultsFound:
            return False
        except NoResultFound:
            return True
