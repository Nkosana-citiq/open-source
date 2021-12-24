from open_source import db
from open_source.core.applicants import Applicant


def get_all_applicants(session):
    search = "https://osource.co.za/assets/uploads/"
    applicants = session.query(Applicant).filter(Applicant.state != Applicant.STATE_DELETED, Applicant.personal_docs.ilike('{}%'.format(search))).all()
    return applicants


def update_applicant(session, applicant):
    old_string = applicant.personal_docs
    new_string = applicant.personal_docs.replace('https://osource.co.za/assets/uploads/', '/home/nocorpgr/open-source/assets/uploads/personal_docs/')
    result = session.execute("""
        Update applicants set personal_docs=:docs where id=:applicant_id
    """, {'docs': applicant.document, 'applicant_id': applicant.id})
    return result.rowcount


def create_certificate():
    with db.transaction() as session:
        applicants = get_all_applicants(session)
        for applicant in applicants:
            update_applicant(session, applicant)


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()