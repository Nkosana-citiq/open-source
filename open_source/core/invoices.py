from open_source import db
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Invoice(db.Base):
    __tablename__ = 'invoices'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    id = Column(Integer, primary_key=True)
    state = Column(Integer, default=1)
    created = Column(DateTime, server_default=func.now())
    payment_date = Column(DateTime)
    number = Column(String(length=255))
    document = Column(String(length=255))
    path = Column(String(length=255))
    amount = Column(String(length=6))
    premium = Column(String(length=6))
    email = Column(String(length=50))
    policy_number = Column(String(length=30))
    number_of_months = Column(String(length=2))
    id_number = Column(String(length=30))
    customer = Column(String(length=50))
    assisted_by = Column(String(length=50))
    address = Column(String(length=100))
    contact = Column(String(length=12))
    branch = Column(String(length=100))
    months_paid = Column(String(length=255))
    payment_type = Column(String(length=10))

    @declared_attr
    def payment_id(cls):
        return Column(Integer, ForeignKey('payments.id'))

    @declared_attr
    def payment(cls):
        return relationship('Payment')

    @declared_attr
    def parlour_id(cls):
        return Column(Integer, ForeignKey('parlours.id'))

    @declared_attr
    def parlour(cls):
        return relationship('Parlour', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'state': self.state,
            'date': self.created,
            'invoice_number': self.number,
            'amount': self.amount,
            'email': self.email,
            'address': self.address,
            'branch': self.branch,
            'path': self.path,
            'premium': self.premium,
            'contact': self.contact,
            'policy_number': self.policy_number,
            'id_number': self.id_number,
            'customer': self.customer,
            'assisted_by': self.assisted_by,
            'number_of_months': self.number_of_months,
            'months_paid': self.months_paid,
            'payment_type': self.payment_type,
            'document': self.document,
            'payment': self.payment.to_dict(),
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
