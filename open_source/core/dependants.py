from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Dependant(db.Base):
    __tablename__ = 'dependants'

    STATE_ARCHIVED= 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    date_of_birth = Column(Date())
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    number = Column(String(length=12))
    date_joined = Column(Date())
    created_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def applicant_id(cls):
        return Column(Integer, ForeignKey('applicants.id'))

    @declared_attr
    def applicant(cls):
        return relationship('Applicant')

    def to_dict(self):
        return {
            'id': self.id,
            'date_of_birth': self.date_of_birth,
            'state': self.state,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'number': self.number,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'date_joined': self.date_joined,
            'relation_to_main_member': self.relation_to_main_member,
            'applicant': self.applicant.to_short_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'date_of_birth': self.date_of_birth,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'number': self.number,
            'date_joined': self.date_joined,
            'relation_to_main_member': self.relation_to_main_member
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
