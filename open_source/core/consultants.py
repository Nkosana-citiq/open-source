from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Consultant(db.Base):
    __tablename__ = 'tbl_applicants'

    STATE_ARCHIVED= 2
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
        return Column(Integer, ForeignKey('tbl_parlour.parlour_id'))

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
