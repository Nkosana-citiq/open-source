from open_source.core.main_members import MainMember
from open_source.core.certificate import Certificate
from open_source.core.extended_members import ExtendedMember
from open_source.core.main_members import MainMember
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from open_source import db
import logging
import os
import uuid

logger = logging.getLogger(__name__)


def update_certificate(session, main_member):
    with db.transaction() as session:
        parlour = session.query(Parlour).filter(Parlour.id == main_member.parlour.id).one_or_none()
        plan = session.query(Plan).filter(Plan.id == main_member.plan.id).one_or_none()
        main_member = session.query(MainMember).filter(MainMember.main_member_id == main_member.id, MainMember.state == MainMember.STATE_ACTIVE).first()

        if main_member:
            extended_members = session.query(ExtendedMember).filter(
                ExtendedMember.main_member_id == main_member.id,
                ExtendedMember.state == ExtendedMember.STATE_ACTIVE).all()

            try:
                canvas = Certificate(uuid.uuid4())
                canvas.set_title(parlour.parlourname)
                canvas.set_address(parlour.address if parlour.address else '')
                canvas.set_contact(parlour.number)
                canvas.set_email(parlour.email)
                canvas.membership_certificate()
                canvas.set_member("Main Member")
                canvas.set_name(' '.join([main_member.first_name, main_member.last_name]))
                canvas.set_id_number(main_member.id_number)
                canvas.set_date_joined(main_member.date_joined)
                canvas.set_date_created(main_member.created_at.date())
                canvas.set_waiting_period(main_member.waiting_period)
                canvas.set_member_contact(main_member.contact)
                canvas.set_current_plan(plan.plan)
                canvas.set_current_premium(plan.premium)
                canvas.set_physical_address(main_member.address if main_member.address else '')

                for extended_member in extended_members:
                    canvas.add_other_members(extended_member)

                if plan.benefits:
                    canvas.set_benefits(plan.benefits)
                canvas.save()
                old_document = main_member.document
                main_member.document = canvas.get_file_path()
                if old_document and os.path.exists(old_document):
                    os.remove(old_document)

            except Exception as e:
                logger.exception("Error, experienced an error while creating certificate.")
                print(e)

    return main_member


def cli():
    with db.transaction() as session:
        main_members = session.query(MainMember).filter(MainMember.state.in_((MainMember.STATE_ACTIVE, MainMember.STATE_ARCHIVED))).all()

        for main_member in main_members:
            update_certificate(session, main_member)
        session.commit()


if __name__ == "__main__":
    cli()