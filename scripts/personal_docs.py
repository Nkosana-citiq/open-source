# from open_source import db
# from open_source.core.main_members import MainMember


# def get_all_main_members(session):
#     main_members = session.query(MainMember).filter(MainMember.state != MainMember.STATE_DELETED).all()
#     return main_members


# def update_applicant(session, applicant):
#     result = session.execute("""
#         Update main_members set personal_docs=:docs where id=:main_member_id
#     """, {'docs': applicant.document, 'main_member_id': applicant.id})
#     return result.rowcount


# def create_certificate():
#     with db.transaction() as session:
#         main_members = get_all_main_members(session)
#         for applicant in main_members:
#             update_applicant(session, applicant)


# def cli():
#     create_certificate()


# if __name__ == '__main__':
#     cli()