from open_source import db
from open_source.core.main_members import MainMember
from open_source.rest import extended_members


def get_all_main_members(session):
    main_members = session.query(MainMember).filter(MainMember.state != MainMember.STATE_DELETED).all()
    return main_members


def update_payments(main_member=None):
    extended_members.update_certificate(main_member)


def create_certificate():
    with db.transaction() as session:
        main_members = get_all_main_members(session)
        for main_member in main_members:
            update_payments(main_member)


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()
