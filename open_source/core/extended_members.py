from typing import Text
from sqlalchemy.sql.sqltypes import Boolean, DECIMAL
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class ExtendedMember(db.Base):
    __tablename__ = 'extended_members'

    STATE_ARCHIVED= 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    state_to_text = {
        STATE_ARCHIVED: 'Archived',
        STATE_ACTIVE: 'Active',
        STATE_DELETED: 'Deleted'
    }

    TYPE_SPOUSE = 4
    TYPE_DEPENDANT = 1
    TYPE_EXTENDED_MEMBER = 2
    TYPE_ADDITIONAL_EXTENDED_MEMBER = 3

    type_to_text = {
        TYPE_SPOUSE: 'Spouse',
        TYPE_DEPENDANT: 'Dependant',
        TYPE_EXTENDED_MEMBER: 'Extended Member',
        TYPE_ADDITIONAL_EXTENDED_MEMBER: 'Additional Extended Member'
    }

    text_to_type = {
        'spouse': TYPE_SPOUSE,
        'dependent': TYPE_DEPENDANT,
        'extended_member': TYPE_EXTENDED_MEMBER,
        'additional_extended_member': TYPE_ADDITIONAL_EXTENDED_MEMBER
    }

    RELATION_CHILD = 12
    RELATION_PARENT = 1
    RELATION_BROTHER = 2
    RELATION_SISTER = 3
    RELATION_NEPHEW = 4
    RELATION_NIECE = 5
    RELATION_AUNT = 6
    RELATION_UNCLE = 7
    RELATION_GRAND_PARENT = 8
    RELATION_WIFE = 9
    RELATION_HUSBAND = 10
    RELATION_COUSIN = 11

    relation_to_text = {
        RELATION_CHILD: 'Child',
        RELATION_PARENT: 'Parent',
        RELATION_BROTHER: 'Brother',
        RELATION_SISTER: 'Sister',
        RELATION_NEPHEW: 'Nephew',
        RELATION_NIECE: 'Niece',
        RELATION_AUNT: 'Aunt',
        RELATION_UNCLE: 'Uncle',
        RELATION_GRAND_PARENT: 'Grand Parent',
        RELATION_WIFE: 'Wife',
        RELATION_HUSBAND: 'Husband',
        RELATION_COUSIN: 'Cousin'
    }

    text_to_relation = {
        'child': RELATION_CHILD,
        'parent': RELATION_PARENT,
        'brother': RELATION_BROTHER,
        'sister': RELATION_SISTER,
        'nephew': RELATION_NEPHEW,
        'niece': RELATION_NIECE,
        'aunt': RELATION_AUNT,
        'Uncle': RELATION_UNCLE,
        'grand_parent': RELATION_GRAND_PARENT,
        'wife': RELATION_WIFE,
        'husband': RELATION_HUSBAND,
        'cousin': RELATION_COUSIN
    }

    id = Column(Integer, primary_key=True)
    date_of_birth = Column(Date())
    state = Column(Integer, default=1)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    type = Column(Integer)
    number = Column(String(length=12))
    id_number = Column(String(length=15))
    relation_to_main_member = Column(Integer)
    is_deceased = Column(Boolean, default=False)
    is_main_member_deceased = Column(Boolean, default=False)
    age_limit_exceeded = Column(Boolean(), default=False)
    age_limit_exception = Column(Boolean(), default=False)
    waiting_period = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())
    date_joined = Column(DateTime, server_default=func.now())

    @declared_attr
    def applicant_id(cls):
        return Column(Integer, ForeignKey('applicants.id'))

    @declared_attr
    def applicant(cls):
        return relationship('Applicant', back_populates='extended_members')

    @property
    def state_text(self):
        return self.state_to_text.get(self.state, 'Undefined')

    @property
    def type_text(self):
        return self.type_to_text.get(self.type, 'Undefined')

    @property
    def relation_text(self):
        return self.relation_to_text.get(self.relation_to_main_member, 'Undefined')

    @staticmethod
    def text_type(text):
        return ExtendedMember.text_to_type.get(text, 'Undefined')

    @staticmethod
    def text_relation(text):
        return ExtendedMember.text_to_relation.get(text, 'Undefined')

    def to_dict(self):
        return {
            'id': self.id,
            'date_of_birth': self.date_of_birth,
            'state': self.state,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'type': self.type,
            'number': self.number,
            'created_at': self.created_at,
            'id_number': self.id_number,
            'modified_at': self.modified_at,
            'date_joined': self.date_joined,
            'age_limit_exceeded': self.age_limit_exceeded,
            'age_limit_exception': self.age_limit_exception,
            'relation_to_main_member': self.relation_to_main_member,
            'waiting_period': self.waiting_period,
            'is_deceased': self.is_deceased,
            'is_main_member_deceased': self.is_main_member_deceased,
            'applicant': self.applicant.to_short_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'date_of_birth': self.date_of_birth,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'type': self.type,
            'number': self.number,
            'id_number': self.id_number,
            'age_limit_exceeded': self.age_limit_exceeded,
            'age_limit_exception': self.age_limit_exception,
            'relation_to_main_member': self.relation_to_main_member,
            'date_joined': self.date_joined,
            'waiting_period': self.waiting_period,
            'is_deceased': self.is_deceased,
            'is_main_member_deceased': self.is_main_member_deceased,
            'applicant': self.applicant.to_short_dict()
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

    def is_archived(self) -> bool:
        return self.state == self.STATE_ARCHIVED

    def make_archived(self):
        self.state = self.STATE_ARCHIVED
        self.on_delete_clean_up()

    def archive(self, session):
        self.make_archived()
        session.commit()