from datetime import datetime
from dateutil.relativedelta import relativedelta
from open_source import db, utils
from open_source.core.applicants import Applicant
from open_source.core.payments import Payment

def get_last_payment(session, applicant_id):
    payment = session.query(Payment).filter(Payment.applicant_id == applicant_id).order_by(Payment.id.desc()).first()
    return payment


def get_all_applicants(session):
    payment = session.query(Applicant).filter(Applicant.state != Applicant.STATE_DELETED).all()
    return payment


def set_state(session, status, applicant_id):
    result = session.execute("""
        Update applicants set status=:status where id=:applicant_id
    """, {'status': status, 'applicant_id': applicant_id})
    return result.rowcount

def update_payments(session, applicant=None):
    last_payment = get_last_payment(session, applicant.id)
    NOW = datetime.now()

    if last_payment:
        if relativedelta(NOW, last_payment.date).months > 3 and NOW.month > last_payment.date.month:
            set_state(session, 'lapsed', applicant.id)
        elif relativedelta(NOW, last_payment.date).months > 1 and NOW.month > last_payment.date.month:
            set_state(session, 'skipped', applicant.id)
        elif relativedelta(NOW, last_payment.date).months > 0 and NOW.month > last_payment.date.month:
            set_state(session, 'unpaid', applicant.id)
        elif relativedelta(NOW, last_payment.date).months == 0 or relativedelta(NOW, last_payment.date).months < 0:
            set_state(session, 'paid', applicant.id)
    else:
        if relativedelta(NOW, applicant.date).months > 3 and NOW.month > applicant.date.month:
            set_state(session, 'lapsed', applicant.id)
        elif relativedelta(NOW, applicant.date).months > 1 or relativedelta(NOW, applicant.date).months == 1 and NOW.month > applicant.date.month:
            set_state(session, 'skipped', applicant.id)
        else:
            set_state(session, 'unpaid', applicant.id)


def update_payment_status():
    with db.transaction() as session:
        applicants = get_all_applicants(session)
        for applicant in applicants:
            update_payments(session, applicant)


def cli():
    update_payment_status()


if __name__ == '__main__':
    cli()
