from sqlalchemy.sql.sqltypes import Boolean
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Applicant(db.Base):
    __tablename__ = 'applicants'

    STATE_ARCHIVED= 2
    STATE_ACTIVE = 1
    STATE_DELETED = 0

    STATUS_LAPSED = 4
    STATUS_SKIPPED = 3
    STATUS_UNPAID= 2
    STATUS_PAID = 1

    status_to_text = {
        STATUS_LAPSED: 'Lapsed',
        STATUS_SKIPPED: 'Skipped',
        STATUS_UNPAID: 'Unpaid',
        STATUS_PAID: 'Paid'
    }

    id = Column(Integer, primary_key=True)
    policy_num = Column(String(length=15))
    address = Column(String(length=100))
    certificate = Column(String(length=250))
    document = Column(Text)
    old_url = Column(Boolean)
    personal_docs = Column(Text)
    state = Column(Integer, default=1)
    status = Column(String(length=15), default="unpaid")
    date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime, server_default=func.now())
    canceled = Column(Integer, default=0)

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour')

    @declared_attr
    def plan_id(cls):
        return Column(Integer, ForeignKey('plans.id'))

    @declared_attr
    def plan(cls):
        return relationship('Plan')

    @declared_attr
    def consultant_id(cls):
        return Column(Integer, ForeignKey('consultants.id'))

    @declared_attr
    def consultant(cls):
        return relationship('Consultant')

    @declared_attr
    def extended_members(cls):
        return relationship('ExtendedMember', back_populates='applicant')

    def to_dict(self):
        return {
            'id': self.id,
            'policy_num': self.policy_num,
            'document': self.document,
            'old_url': self.old_url,
            'personal_docs':self.personal_docs,
            'address': self.address,
            'certificate': self.certificate,
            'date': self.date,
            'state': self.state,
            'status': self.status.capitalize(),
            'canceled': self.canceled,
            "modified": self.modified_at,
            'created': self.created_at,
            'parlour': self.parlour.to_dict(),
            'plan': self.plan.to_short_dict(),
            'consultant': self.consultant.to_short_dict()
        }

    def to_short_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'policy_num': self.policy_num,
            'certificate': self.certificate,
            'address': self.address,
            'document': self.document,
            'old_url': self.old_url,
            'personal_docs':self.personal_docs,
            'date': self.date,
            'status': self.status.capitalize(),
            'canceled': self.canceled,
            'plan': self.plan.to_short_dict(),
            'consultant': self.consultant.to_short_dict()
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

    def on_delete_clean_up(self, session):
        for extended_member in self.extended_members:
            extended_member.delete(session)
    
    def is_archived(self) -> bool:
        return self.state == self.STATE_ARCHIVED

    def make_archived(self):
        self.state = self.STATE_ARCHIVED

