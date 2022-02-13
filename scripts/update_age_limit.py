from open_source.core.applicants import Applicant
from open_source.core.certificate import Certificate
from open_source.core.extended_members import ExtendedMember
from open_source.core.main_members import MainMember
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from open_source import db

import datetime
import falcon
import logging

from dateutil.relativedelta import relativedelta


logger = logging.getLogger(__name__)


def get_date_of_birth(self, date_of_birth=None, id_number=None):
    current_year = datetime.datetime.now().year
    year_string = str(current_year)[2:]
    century = 19
    if date_of_birth:
        return date_of_birth.replace('T', " ")[:10]
    if id_number:
        if 0 <= int(id_number[:2]) <= int(year_string):
            century = 20
        return '{}{}-{}-{}'.format(century,id_number[:2], id_number[2:4], id_number[4:-6])[:10]


def age_limit_per_extended_member_type(extended_member, plan):

    if extended_member.type == 1:
        return plan.dependant_minimum_age, plan.dependant_maximum_age
    if extended_member.type == 2:
        return plan.extended_minimum_age, plan.extended_maximum_age
    if extended_member.type == 4:
        return plan.spouse_minimum_age, plan.spouse_maximum_age
    if extended_member.type == 3:
        return plan.additional_extended_minimum_age, plan.additional_extended_maximum_age


def update_extended_members_age_limit(session, plan, applicant):
    extended_members = session.query(ExtendedMember).filter(ExtendedMember.applicant_id == applicant.id).all()

    if extended_members:
        for extended_member in extended_members:
            age_limit_exceeded = False
            min_age_limit, max_age_limit = age_limit_per_extended_member_type(extended_member, plan)

            try:
                if extended_member.date_of_birth:
                    date_of_birth = extended_member.date_of_birth
                elif extended_member.id_number:
                    if int(extended_member.id_number[0:2]) > 21:
                        number = '19{}'.format(extended_member.id_number[0:2])
                    else:
                        number = '20{}'.format(extended_member.id_number[0:2])
                    date_of_birth = '{}-{}-{}'.format(number, extended_member.id_number[2:4], extended_member.id_number[4:6])
                dob = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            except:
                continue

            now = datetime.datetime.now().date()

            age = relativedelta(now, dob)

            years = "{}".format(age.years)

            if max_age_limit:
                if len(years) > 2 and int(years[2:4]) > max_age_limit:
                    age_limit_exceeded = True
                elif int(years) > max_age_limit:
                    age_limit_exceeded = True

            if min_age_limit:
                if len(years) > 2 and int(years[2:4]) < min_age_limit:
                    age_limit_exceeded = True
                elif int(years) < min_age_limit:
                    age_limit_exceeded = True

            if age_limit_exceeded == True:
                extended_member.age_limit_exceeded = True
            else:
                extended_member.age_limit_exceeded = False
            session.commit()


def update_age_limit(session, applicant):
    plan = session.query(Plan).filter(Plan.id == applicant.plan.id).one_or_none()
    main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id).one_or_none()

    if main_member:
        age_limit_exceeded = False
        min_age_limit = plan.member_minimum_age
        max_age_limit = plan.member_maximum_age
        id_number = main_member.id_number

        if id_number:
            if not plan:
                raise falcon.HTTPBadRequest(title="Plan not found", description="Plan does not exist.")
    
            if int(id_number[0:2]) > 21:
                number = '19{}'.format(id_number[0:2])
            else:
                number = '20{}'.format(id_number[0:2])
            try:
                date_of_birth = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])

                dob = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            except:
                ...

            now = datetime.datetime.now().date()

            age = relativedelta(now, dob)
    
            years = "{}".format(age.years)

            if max_age_limit:
                if len(years) > 2 and int(years[2:4]) > max_age_limit:
                    age_limit_exceeded = True
                elif int(years) > max_age_limit:
                    age_limit_exceeded = True
    
            if min_age_limit:
                if len(years) > 2 and int(years[2:4]) < min_age_limit:
                    age_limit_exceeded = True
                elif int(years) < min_age_limit:
                    age_limit_exceeded = True
    
            if age_limit_exceeded == True:
                main_member.age_limit_exceeded = True
            else:
                main_member.age_limit_exceeded = False
            update_extended_members_age_limit(session, plan, applicant)


def cli():
    with db.transaction() as session:
        applicants = session.query(Applicant).filter(Applicant.state.in_((Applicant.STATE_ACTIVE, Applicant.STATE_ARCHIVED))).all()
        for applicant in applicants:
            try:
                update_age_limit(session, applicant)
            except:
                continue


if __name__ == "__main__":
    cli()
