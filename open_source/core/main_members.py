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
    age_limit_exceeded = Column(Boolean(), default=False)
    age_limit_exception = Column(Boolean(), default=False)
    state = Column(Integer, default=1)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    contact = Column(String(length=12))
    is_deceased = Column(Boolean, default=False)
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
    
    def localize_contact(self):
        return ''.join(['+27', self.contact[1:]]) if len(self.contact) == 10 else self.contact

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
            'is_deceased': self.is_deceased,
            'age_limit_exceeded': self.age_limit_exceeded,
            'age_limit_exception': self.age_limit_exception,
            'extended_member_limit': self.extended_member_limit(),
            'parlour': self.parlour.to_dict()  if self.parlour else {} ,
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
            'age_limit_exceeded': self.age_limit_exceeded,
            'age_limit_exception': self.age_limit_exception,
            'extended_member_limit': self.extended_member_limit(),
            'date_joined': self.date_joined,
            'is_deceased': self.is_deceased,
            'created_at': self.created_at,
            'applicant': self.applicant.to_short_dict() if self.applicant else {}
        }
    
    def save(self, session):
        session.add(self)
        session.commit()

    def is_deleted(self) -> bool:
        return self.state == self.STATE_DELETED

    def make_deleted(self):
        self.state = self.STATE_DELETED
        self.on_delete_clean_up()

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

    def extended_member_limit(self):
        with db.no_transaction() as session:
            sql = "select * from extended_members where id={} and age_limit_exceeded=1 AND state=1".format(self.id)
            result = session.execute(sql)
            return result.rowcount


    def on_delete_clean_up(self):
        self.applicant.state = self.applicant.STATE_ARCHIVED
