from datetime import datetime
from dateutil.relativedelta import relativedelta
from open_source import db, utils
from open_source.core.main_members import MainMember
from open_source.core.payments import Payment

def get_last_payment(session, main_member_id):
    payment = session.query(Payment).filter(Payment.main_member_id == main_member_id).order_by(Payment.id.desc()).first()
    return payment


def get_all_main_members(session):
    main_members = session.query(MainMember).filter(MainMember.state != MainMember.STATE_DELETED).all()
    return main_members


def set_state(session, status, main_member_id, state):

    if status == "lapsed":
        state = 2
        set_state_main_members(session, main_member_id, state)
    result = session.execute("""
        Update main_members set status=:status, state=:state where id=:main_member_id
    """, {'status': status, 'main_member_id': main_member_id, 'state': state})
    return result.rowcount

def set_state_main_members(session, main_member_id, state):
    result = session.execute("""
        Update main_members set state=:state where main_member_id=:main_member_id
    """, {'state': state, 'main_member_id': main_member_id})
    return result.rowcount

def update_payments(session, main_member=None):
    last_payment = get_last_payment(session, main_member.id)
    NOW = datetime.now()

    if last_payment:
        if relativedelta(NOW, last_payment.date.replace(day=1)).months > 3:
            set_state(session, 'lapsed', main_member.id, main_member.state)
        elif relativedelta(NOW, last_payment.date.replace(day=1)).months > 1:
            set_state(session, 'skipped', main_member.id, main_member.state)
        elif relativedelta(NOW, last_payment.date.replace(day=1)).months > 0 or relativedelta(NOW, last_payment.date.replace(day=1)).months == 0 and NOW.month > last_payment.date.month:
            set_state(session, 'unpaid', main_member.id, main_member.state)
        else:
            set_state(session, 'paid', main_member.id, main_member.state)
    else:
        if relativedelta(NOW, main_member.date.replace(day=1)).months > 3 or relativedelta(NOW, main_member.date.replace(day=1)).months == 3 and NOW.month > main_member.date.month:
            set_state(session, 'lapsed', main_member.id, main_member.state)
        elif relativedelta(NOW, main_member.date.replace(day=1)).months == 0:
            set_state(session, 'unpaid', main_member.id, main_member.state)
        else:
            set_state(session, 'skipped', main_member.id, main_member.state)


def update_payment_status():
    with db.transaction() as session:
        main_members = get_all_main_members(session)
        for main_member in main_members:
            update_payments(session, main_member)


def cli():
    update_payment_status()


if __name__ == '__main__':
    cli()