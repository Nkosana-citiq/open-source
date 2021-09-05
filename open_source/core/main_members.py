from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class MainMember(db.Base):
    __tablename__ = 'main_members'

    STATE_ARCHIVED= 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    id_number = Column(String(length=15))
    date_of_birth = Column(Date())
    state = Column(Integer, default=1)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    contact = Column(String(length=12))
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())
    date_joined = Column(DateTime, server_default=func.now())

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    @declared_attr
    def applicant_id(cls):
        return Column(Integer, ForeignKey('applicants.id'))

    @declared_attr
    def applicant(cls):
        return relationship('Applicant')

    def to_dict(self):
        return {
            'id': self.id,
            'id_number': self.id_number,
            'date_of_birth': self.date_of_birth,
            'state': self.state,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'contact': self.contact,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'date_joined': self.date_joined,
            'parlour': self.parlour.to_dict(),
            'applicant': self.applicant.to_short_dict() if self.applicant else {} 
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'id_number': self.id_number,
            'date_of_birth': self.date_of_birth,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'contact': self.contact,
            'date_joined': self.date_joined
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
