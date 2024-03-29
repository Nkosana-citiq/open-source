from datetime import datetime


from sqlalchemy import event, DDL
from open_source.core import parlours, consultants, plans, applicants, main_members, extended_members, audit, certificate, admins, notifications
from open_source import db



def before_update(mapper, connection, target):
    if hasattr(target, 'modified_at'):
        target.modified_at = datetime.now()


def before_insert(mapper, connection, target):
    now = datetime.now()
    # cake sets modified on insert
    if hasattr(target, 'modified_at'):
        target.modified = now
    if hasattr(target, 'created_at'):
        target.created = now

# TODO: Use mysql functions when we are off cake
# register before_update on all table classes
for clazz in db.Base.__subclasses__():
    event.listen(clazz, 'before_update', before_update)
    event.listen(clazz, 'before_insert', before_insert)