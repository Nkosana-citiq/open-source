from open_source import db
from open_source.core.main_members import MainMember
from open_source.core.extended_members import ExtendedMember
from open_source.core.main_members import MainMember


def delete_main_member(session, main_member_id):
    sql = """
        delete from main_members where id=:main_member_id
    """
    result = session.execute(sql, {'main_member_id': main_member_id})
    return result.rowcount


def create_extended_member(session, main_member):
    extended_member = ExtendedMember(
        first_name = main_member.first_name,
        last_name = main_member.last_name,
        number = main_member.contact,
        main_member_id = main_member.id,
        date_joined = main_member.date_joined,
        created_at = main_member.created_at,
        state = main_member.state,
        modified_at = main_member.modified_at,
        type = ExtendedMember.TYPE_SPOUSE,
        relation_to_main_member = ExtendedMember.RELATION_WIFE,
        age_limit_exceeded = 0,
        age_limit_exception = 0,
        id_number = main_member.id_number
    )

    session.add(extended_member)
    delete_main_member(session, main_member.id)


def create_certificate():
    with db.transaction() as session:
        main_members = session.query(MainMember).filter(MainMember.state != MainMember.STATE_DELETED).all()
        for main_member in main_members:
            create_extended_member(session, main_member)
        session.commit()


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()