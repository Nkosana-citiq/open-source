from typing import Dict, Any, Text
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
    waiting_period = Column(Integer, default=0)
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
        if len(self.contact) == 10:
            return ''.join(['+27', self.contact[1:]])
        elif len(self.contact) < 10:
            return ''.join(['+27', self.contact])
        return self.contact

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
            'waiting_period': self.waiting_period,
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
            'waiting_period': self.waiting_period,
            'age_limit_exceeded': self.age_limit_exceeded,
            'age_limit_exception': self.age_limit_exception,
            'extended_member_limit': self.extended_member_limit(),
            'date_joined': self.date_joined,
            'is_deceased': self.is_deceased,
            'created_at': self.created_at,
            'applicant': self.applicant.to_short_dict() if self.applicant else {}
        }
    
    @classmethod
    def rest_get_many(cls, session, params: Dict[str, Any], user, **kwargs) -> Dict[str, Any]:
        return cls._paginated_result(params, user, cls.get_many_query)

    @classmethod
    def _paginated_results(cls, params: Dict[str, Any],result_query) -> Dict[str, Any]:

        offset = params.pop('offset', 0)
        limit = params.pop('limit', 20)
        total = 0

        is_lookup = params.pop('is_lookup', 'no')
        is_lookup = is_lookup in ('yes', 'y', 't', 'true', '1')

        if result_query:
            total = len([entity for entity in result_query])
            result_query = result_query.offset(offset)
            result_query = result_query.limit(limit)

            result = [entity.to_dict() for entity in result_query]

        else:
            result = []

        return {
            "offset": offset,
            "limit": limit,
            "count": len(result),
            "total": total,
            "result": result
        }

    @classmethod
    def _paginated_search_results(cls, params: Dict[str, Any],result_query) -> Dict[str, Any]:

        offset = params.pop('offset', 0)
        limit = params.pop('limit', 20)
        total = 0

        is_lookup = params.pop('is_lookup', 'no')
        is_lookup = is_lookup in ('yes', 'y', 't', 'true', '1')

        if result_query:
            total = len([entity for entity in result_query])
            result_query = result_query.offset(offset)
            result_query = result_query.limit(limit)

            result = [entity[0].to_dict() for entity in result_query if entity]

        else:
            result = []

        return {
            "offset": offset,
            "limit": limit,
            "count": len(result),
            "total": total,
            "result": result
        }

    def save(self, session):
        session.add(self)
        session.commit()

    def is_deleted(self) -> bool:
        return self.state == self.STATE_DELETED

    def make_deleted(self, session):
        self.state = self.STATE_DELETED
        self.on_delete_clean_up(session)

    def delete(self, session):
        self.make_deleted(session)
        session.commit()

    def is_archived(self) -> bool:
        return self.state == self.STATE_ARCHIVED

    def make_archived(self):
        self.state = self.STATE_ARCHIVED
        self.on_archive_clean_up()

    def archive(self, session):
        self.make_archived()
        session.commit()

    def extended_member_limit(self):
        with db.no_transaction() as session:
            sql = "select * from extended_members where applicant_id={} and age_limit_exceeded=1 AND age_limit_exception=0 AND state=1".format(self.applicant_id)
            result = session.execute(sql)
            return result.rowcount

    def on_delete_clean_up(self, session):
        self.applicant.delete(session)

    def on_archive_clean_up(self):
        self.applicant.make_archived()