from datetime import datetime
from dateutil.relativedelta import relativedelta
from open_source import db, utils
from open_source.core.applicants import Applicant
from open_source.core.main_members import MainMember
from open_source.core.payments import Payment


def get_all_applicants(session):
    payment = session.query(Applicant).filter(Applicant.state != Applicant.STATE_DELETED).all()
    return payment


def update_payment_status():
    with db.transaction() as session:
        applicants = get_all_applicants(session)
        for applicant in applicants:
            Payment.update_payment_status(session, applicant)


def cli():
    update_payment_status()


if __name__ == '__main__':
    cli()
