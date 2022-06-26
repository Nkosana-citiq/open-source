from random import choice, randint
import base64
import hashlib

from open_source import config
from open_source import db
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Role(db.Base):
    __tablename__ = 'roles'

    STATE_ACTIVE = 1
    STATE_DELETED = 0

    IS_ADMIN = 1
    IS_PARLOUR = 2
    IS_CONSULTANT = 3

    id = Column(Integer, primary_key=True)
    name = Column(String(length=30))

    @declared_attr
    def users(cls):
        return relationship("User", back_populates="role")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
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
