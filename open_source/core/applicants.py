from typing import Text
from falcon import constants
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Applicant(db.Base):
    __tablename__ = 'applicants'

    STATE_ARCHIVED= 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    policy_num = Column(String(length=15))
    document = Column(Date())
    state = Column(Integer, default=1)
    status = Column(String(length=15), default="unpaid")
    date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())
    canceled = Column(Integer, default=0)

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.parlour_id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    @declared_attr
    def plan_id(cls):
        return Column(Integer, ForeignKey('plans.plan_id'))

    @declared_attr
    def plan(cls):
        return relationship('Plan')

    @declared_attr
    def consultant_id(cls):
        return Column(Integer, ForeignKey('consultants.consultant_id'))

    @declared_attr
    def consultant(cls):
        return relationship('Consultant')

    def to_dict(self):
        print("Consultant ID: ", self.consultant_id)
        return {
            'id': self.id,
            'policy_num': self.policy_num,
            'document': self.document,
            'date': self.date,
            'state': self.state,
            'status': self.status,
            'canceled': self.canceled,
            "modified": self.modified_at,
            'created': self.created_at,
            'parlour': self.parlour.to_dict(),
            'plan': self.plan.to_short_dict(),
            'consultant': self.consultant.to_short_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.plan_id,
            'policy_num': self.policy_num,
            'date': self.date,
            'status': self.status,
            'canceled': self.canceled
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
