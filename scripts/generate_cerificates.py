from open_source import db
from open_source.core.applicants import Applicant
from open_source.rest import extended_members


def get_all_applicants(session):
    applicants = session.query(Applicant).filter(Applicant.state != Applicant.STATE_DELETED).all()
    return applicants


def update_payments(applicant=None):
    extended_members.update_certificate(applicant)


def create_certificate():
    with db.transaction() as session:
        applicants = get_all_applicants(session)
        for applicant in applicants:
            update_payments(applicant)


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()
