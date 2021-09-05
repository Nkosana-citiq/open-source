from datetime import datetime
import json

from typing import Text
from open_source import db
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship



class AuditLog(db.Base):
    __tablename__ = 'auditlogs'

    id = Column(Integer, primary_key=True)
    data_name = Column(String(100))
    data_type = Column(String(100))
    data_old = Column(Text)
    data_new = Column(Text)
    notes = Column(Text)
    created = Column(DateTime, default=datetime.now())


class AuditLogClient(object):

    @classmethod
    def save_log(cls, session, user_id, email, data_name=None, data_old=None, data_new=None, notes=None, data_classname=None):
        session.add(AuditLog(
            user_id=user_id,
            email=email,
            data_old=json.dumps(data_old) if data_old else None,
            data_new=json.dumps(data_new) if data_new else None,
            data_name=data_name,
            data_type=data_classname,
            notes=notes
        ))
