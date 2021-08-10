from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Plan(db.Base):
    __tablename__ = 'tbl_plans'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    plan_id = Column(Integer, primary_key=True)
    plan = Column(String(length=200))
    cover = Column(DECIMAL(2))
    premium = Column(DECIMAL(2))
    state = Column(Integer, default=1)
    member_age_restriction = Column(String(length=2))
    member_minimum_age = Column(String(length=2))
    member_maximum_age = Column(String(length=2))
    beneficiaries = Column(String(length=2))
    consider_age = Column(Boolean)
    minimum_age = Column(String(length=2))
    maximum_age = Column(String(length=2))
    has_benefits = Column(Boolean)
    benefits = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('tbl_parlour.parlour_id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    @classmethod
    def get_plan(cls, session, plan_id):
        query = session.query(Plan).filter(Plan.plan_id == plan_id, Plan.state != cls.STATE_DELETED)
        return cls.with_relationships(query).one_or_none()

    def to_dict(self):
        return {
            'id': self.plan_id,
            'plan': self.plan,
            'cover': self.cover,
            'premium': self.premium,
            'member_age_restriction': self.member_age_restriction,
            'member_minimum_age': self.member_minimum_age,
            'member_maximum_age': self.member_maximum_age,
            'beneficiaries': self.beneficiaries,
            'consider_age': self.consider_age,
            'minimum_age': self.minimum_age,
            'maximum_age': self.maximum_age,
            'has_benefits': self.has_benefits,
            'benefits': self.benefits,
            "modified": self.modified_at,
            'created': self.created_at,
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
