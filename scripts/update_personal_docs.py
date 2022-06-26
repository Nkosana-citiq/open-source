from open_source import db
from open_source.core import main_members
from open_source.core.main_members import MainMember


def get_all_main_members(session):
    search = "https://osource.co.za/assets/uploads/"
    main_members = session.query(MainMember).filter(MainMember.state != MainMember.STATE_DELETED, MainMember.personal_docs.ilike('{}%'.format(search))).all()
    return main_members


def update_main_member(session, main_member):
    # old_string = main_member.personal_docs
    # main_member.personal_docs = main_member.personal_docs.replace('https://osource.co.za/assets/uploads/', '/home/nocorpgr/open-source/assets/uploads/personal_docs/')
    result = session.execute("""
        Update main_members set personal_docs=:docs where id=:main_member_id
    """, {'docs': main_member.document, 'main_member_id': main_member.id})
    return result.rowcount


def create_certificate():
    with db.transaction() as session:
        main_members = get_all_main_members(session)
        for main_member in main_members:
            update_main_member(session, main_member)


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()