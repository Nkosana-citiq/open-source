from datetime import datetime
from dateutil.relativedelta import relativedelta

from open_source import db
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
    created = Column(DateTime, server_default=func.now())

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
    def main_member_id(cls):
        return Column(Integer, ForeignKey('main_members.id'))

    @declared_attr
    def main_member(cls):
        return relationship('MainMember')

    def to_dict(self):
        return {
            'id': self.plan_id,
            'created': self.date,
            'state': self.state,
            'payment_type': self.payment_type,
            'main_member': self.main_member.to_short_dict(),
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
    def get_last_payment(session, main_member_id):
        payment = session.query(Payment).filter(Payment.main_member_id == main_member_id).order_by(Payment.id.desc()).first()
        return payment

    @staticmethod
    def set_status(session, status, main_member_id):
        result = session.execute("""
            Update main_members set status=:status where id=:main_member_id
        """, {'status': status, 'main_member_id': main_member_id})
        return result.rowcount

    @staticmethod
    def update_payment_status(session, main_member=None):
        last_payment = Payment.get_last_payment(session, main_member.id)
        main_member_date = main_member.date.date() or None
        NOW = datetime.now()

        if last_payment:
            last_payment_date = last_payment.date.date() or None
            if relativedelta(NOW, last_payment_date.replace(day=1)).months > 3 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'lapsed', main_member.id)
                main_member.state = main_member.STATE_ARCHIVED
                main_member = session.query(MainMember).filter(MainMember.id == main_member.id).order_by(MainMember.id.desc()).first()
                if main_member:
                    main_member.state = MainMember.STATE_ARCHIVED
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months > 1 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'skipped', main_member.id)
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months > 0 and NOW.date() > last_payment.date.date():
                Payment.set_status(session, 'unpaid', main_member.id)
            elif relativedelta(NOW, last_payment_date.replace(day=1)).months == 0 or relativedelta(NOW, last_payment.date).months < 0:
                Payment.set_status(session, 'paid', main_member.id)
        else:
            if relativedelta(NOW, main_member_date.replace(day=1)).months > 3:
                Payment.set_status(session, 'lapsed', main_member.id)
                main_member.state = MainMember.STATE_ARCHIVED
                main_member = session.query(MainMember).filter(MainMember.id == main_member.id).order_by(MainMember.id.desc()).first()
                if main_member:
                    main_member.state = MainMember.STATE_ARCHIVED
            elif relativedelta(NOW, main_member_date.replace(day=1)).months > 0:
                Payment.set_status(session, 'skipped', main_member.id)
            else:
                Payment.set_status(session, 'unpaid', main_member.id)
