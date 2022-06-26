from open_source import db
from open_source.core.main_members import MainMember
from open_source.core.extended_members import ExtendedMember
from open_source.rest.extended_members import update_certificate

def get_all_members(session):
    members = session.query(MainMember).filter(MainMember.waiting_period > 0, MainMember.state != MainMember.STATE_DELETED).all()
    return members


def update_extended_members_waiting_period(session, main_member_id):
    extended_members = session.query(ExtendedMember).filter(
        ExtendedMember.main_member_id == main_member_id,
        ExtendedMember.state != ExtendedMember.STATE_DELETED,
        ExtendedMember.waiting_period > 0).all()

    for extended_member in extended_members:
        extended_member.waiting_period -= 1


def update_main_members_waiting_period(session, main_member):
    main_member.waiting_period -= 1
    main_member_id = main_member.id
    update_extended_members_waiting_period(session, main_member_id)
    main_member = update_certificate(main_member)


def update_waiting_period():
    with db.transaction() as session:
        main_members = get_all_members(session)
        for main_member in main_members:
            update_main_members_waiting_period(session, main_member)
        session.commit()

def cli():
    update_waiting_period()


if __name__ == '__main__':
    cli()