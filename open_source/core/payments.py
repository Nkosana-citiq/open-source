from datetime import datetime
from dateutil.relativedelta import relativedelta

from open_source import db
from open_source.core.applicants import Applicant
from open_source.core.main_members import MainMember

from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Payment(db.Base):
    __tablename__ = 'payments'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    state = Column(Integer, default=1)
    payment_type = Column(String(),)
    date = Column(DateTime, server_default=func.now())

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
    def applicant_id(cls):
        return Column(Integer, ForeignKey('applicants.id'))

    @declared_attr
    def applicant(cls):
        return relationship('Applicant')

    def to_dict(self):
        return {
            'id': self.plan_id,
            'created': self.date,
            'state': self.state,
            'payment_type': self.payment_type,
            'applicant': self.applicant.to_short_dict(),
            'plan': self.plan.to_short_dict(),
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

    @staticmethod
    def get_last_payment(session, applicant_id):
        payment = session.query(Payment).filter(Payment.applicant_id == applicant_id).order_by(Payment.id.desc()).first()
        return payment

    @staticmethod
    def set_status(session, status, applicant_id):
        result = session.execute("""
            Update applicants set status=:status where id=:applicant_id
        """, {'status': status, 'applicant_id': applicant_id})
        return result.rowcount

    @staticmethod
    def update_payment_status(session, applicant=None):
        last_payment = Payment.get_last_payment(session, applicant.id)
        applicant_date = applicant.date.date() or None
        NOW = datetime.now()

        if last_payment:
            last_payment_date = last_payment.date.date() or None
            if relativedelta(NOW, last_payment_date.replace(day=1)).months > 3 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'lapsed', applicant.id)
                applicant.state = Applicant.STATE_ARCHIVED
                main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id).order_by(MainMember.id.desc()).first()
                if main_member:
                    main_member.state = MainMember.STATE_ARCHIVED
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months > 1 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'skipped', applicant.id)
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months > 0 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'unpaid', applicant.id)
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months == 0 or relativedelta(NOW, last_payment.date).months < 0:
                Payment.set_status(session, 'paid', applicant.id)
        else:
            if relativedelta(NOW, applicant_date.replace(day=1)).months > 3:
                Payment.set_status(session, 'lapsed', applicant.id)
                applicant.state = Applicant.STATE_ARCHIVED
                main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id).order_by(MainMember.id.desc()).first()
                if main_member:
                    main_member.state = MainMember.STATE_ARCHIVED
            elif relativedelta(NOW, applicant_date.replace(day=1)).months > 0:
                Payment.set_status(session, 'skipped', applicant.id)
            else:
                Payment.set_status(session, 'unpaid', applicant.id)
