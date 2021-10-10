from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Plan(db.Base):
    __tablename__ = 'plans'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    plan = Column(String(length=200))
    cover = Column(DECIMAL(2))
    premium = Column(DECIMAL(2))
    underwriter_premium = Column(DECIMAL(2))
    state = Column(Integer, default=1)
    main_members = Column(String(length=2))
    member_age_restriction = Column(String(length=2))
    member_minimum_age = Column(String(length=2))
    member_maximum_age = Column(String(length=2))

    spouse = Column(String(length=2))
    spouse_age_restriction = Column(String(length=2))
    spouse_minimum_age = Column(String(length=2))
    spouse_maximum_age = Column(String(length=2))

    extended_members = Column(String(length=2))
    extended_age_restriction = Column(Boolean)
    extended_minimum_age = Column(String(length=2))
    extended_maximum_age = Column(String(length=2))
    beneficiaries = Column(String(length=2))
    consider_age = Column(Boolean)
    dependant_minimum_age = Column(String(length=2))
    dependant_maximum_age = Column(String(length=2))
    additional_extended_members = Column(String(length=2))
    additional_extended_consider_age = Column(Boolean)
    additional_extended_minimum_age = Column(String(length=2))
    additional_extended_maximum_age = Column(String(length=2))
    has_benefits = Column(Boolean)
    benefits = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan,
            'cover': self.cover,
            'premium': self.premium,
            'underwriter_premium': self.underwriter_premium,
            'main_members': self.main_members,
            'member_age_restriction': self.member_age_restriction,
            'member_minimum_age': self.member_minimum_age,
            'member_maximum_age': self.member_maximum_age,
            'extended_members': self.extended_members,
            'extended_age_restriction': self.extended_age_restriction,
            'extended_minimum_age': self.extended_minimum_age,
            'extended_maximum_age': self.extended_maximum_age,
            'dependants': self.beneficiaries,
            'consider_age': self.consider_age,
            'dependant_minimum_age': self.dependant_minimum_age,
            'dependant_maximum_age': self.dependant_maximum_age,
            'additional_extended_members': self.additional_extended_members,
            'additional_extended_consider_age': self.additional_extended_consider_age,
            'additional_extended_minimum_age': self.additional_extended_minimum_age,
            'additional_extended_maximum_age': self.additional_extended_maximum_age,
            'has_benefits': self.has_benefits,
            'benefits': self.benefits,
            "modified": self.modified_at,
            'created': self.created_at,
            'state': self.state,
            'parlour': self.parlour.to_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'plan': self.plan,
            'cover': self.cover,
            'premium': self.premium,
            'underwriter_premium': self.underwriter_premium,
            'main_members': self.main_members,
            'extended_members': self.extended_members,
            'member_age_restriction': self.member_age_restriction,
            'member_minimum_age': self.member_minimum_age,
            'member_maximum_age': self.member_maximum_age,
            'extended_age_restriction': self.extended_age_restriction,
            'extended_minimum_age': self.extended_minimum_age,
            'extended_maximum_age': self.extended_maximum_age,
            'dependant_minimum_age': self.dependant_minimum_age,
            'dependant_maximum_age': self.dependant_maximum_age,
            'additional_extended_members': self.additional_extended_members,
            'additional_extended_consider_age': self.additional_extended_consider_age,
            'additional_extended_minimum_age': self.additional_extended_minimum_age,
            'additional_extended_maximum_age': self.additional_extended_maximum_age,
            'has_benefits': self.has_benefits,
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
