from open_source import db
from open_source.core import dependants
from open_source.core.dependants import Dependant
from open_source.core.extended_members import ExtendedMember
from open_source.core.main_members import MainMember


def get_all_dependant(session):
    dependants = session.query(Dependant).all()
    return dependants


def create_extended_member(session, dependant):
    extended_member = ExtendedMember(
        first_name = dependant.first_name,
        last_name = dependant.last_name,
        number = dependant.number,
        applicant_id = dependant.applicant_id,
        date_joined = dependant.date_joined,
        created_at = dependant.created_at,
        state = 1,
        modified_at = dependant.created_at,
        type = ExtendedMember.TYPE_DEPENDANT,
        relation_to_main_member = ExtendedMember.RELATION_PARENT,
        age_limit_exceeded = 0,
        age_limit_exception = 0,
        date_of_birth = dependant.date_of_birth
    )
    session.add(extended_member)


def create_certificate():
    with db.transaction() as session:
        dependants = get_all_dependant(session)
        for dependant in dependants:
            create_extended_member(session, dependant)
        session.commit()


def cli():
    create_certificate()


if __name__ == '__main__':
    cli()