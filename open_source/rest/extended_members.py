from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from open_source.core import main_members
from open_source.core import extended_members
from open_source.core.main_members import MainMember
from sqlalchemy.orm import relation

from open_source.core.extended_members import ExtendedMember
from open_source.core.applicants import Applicant
from open_source.core.certificate import Certificate
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from falcon_cors import CORS

import falcon
import os
import json
import logging
import uuid

from open_source import db

from open_source.core.applicants import Applicant

from za_id_number.za_id_number import SouthAfricanIdentityValidate


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)


def check_age_limit(extended_members, plan):
    result = []
    for extended_member in extended_members:
        if extended_member.type == 0:
            age_limit = 120
        elif extended_member.type == 1:
            age_limit = plan.dependant_maximum_age
        elif extended_member.type == 2:
            age_limit = plan.additional_extended_maximum_age
        elif extended_member.type == 3:
            age_limit = plan.additional_extended_maximum_age

        dob = extended_member.date_of_birth
        dob = datetime.strptime(dob, "%Y-%m-%d")
        now = datetime.now()

        age = relativedelta(now, dob)

        years = "{}".format(age.years)

        if len(years) > 2 and int(years[2:4]) > age_limit:
            extended_member.age_limit_exceeded = True
        elif int(years) > age_limit:
            extended_member.age_limit_exceeded = True
        result.append(extended_member)
    return result


class ExtendedMemberGetEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        with db.transaction() as session:
            extended_member = session.query(ExtendedMember).filter(
                ExtendedMember.id == id,
                ExtendedMember.state == ExtendedMember.STATE_ACTIVE
            ).first()

            if extended_member is None:
                raise falcon.HTTPNotFound(title="Not Found", description="Member Not Found")

            resp.body = json.dumps(extended_member.to_dict(), default=str)


class ExtendedMembersGetAllEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                notice = None

                if "notice" in req.params:
                        notice = req.params.pop("notice")

                applicant = session.query(Applicant).filter(
                    Applicant.id == id
                ).one_or_none()

                if not applicant:
                    raise falcon.HTTPBadRequest()

                plan = applicant.plan
                extended_members = session.query(ExtendedMember).filter(
                    ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
                    ExtendedMember.applicant_id == applicant.id
                ).all()

                if notice:
                     extended_members = session.query(ExtendedMember).filter(
                        ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
                        ExtendedMember.age_limit_exceeded == True,
                        ExtendedMember.applicant_id == applicant.id
                    ).all()
                if not extended_members:
                    extended_members = session.query(ExtendedMember).filter(
                        ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
                        ExtendedMember.applicant_id == applicant.id
                    ).all()

                if not extended_members:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([extended_member.to_dict() for extended_member in extended_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Extended Members for user with ID {}.".format(id))


class ExtendedMemberPutAgeLimitExceptionEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:

                extended_member = session.query(ExtendedMember).filter(
                    ExtendedMember.id == id,
                    ExtendedMember.state == ExtendedMember.STATE_ACTIVE).first()

                if not extended_member:
                    raise falcon.HTTPNotFound(title="Extended member not found", description="Could not find Applicant with given ID.")

                extended_member.age_limit_exception = req.get("age_limit_exception")

                extended_member.save(session)

                resp.body = json.dumps(extended_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class ExtendedMembersPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def get_date_of_birth(self, date_of_birth=None, id_number=None):
        current_year = datetime.now().year
        year_string = str(current_year)[2:]
        century = 19
        if date_of_birth:
            return date_of_birth.replace('T', " ")[:10]
        if id_number:
            if 0 <= int(id_number[:2]) <= int(year_string):
                century = 20
            return '{}{}-{}-{}'.format(century,id_number[:2], id_number[2:4], id_number[4:-6])[:10]

    def get_date_joined(self, date_joined):
        return date_joined.replace('T', " ")[:10]

    def on_post(self, req, resp):
        req = json.load(req.bounded_stream)

        try:
            with db.transaction() as session:
                applicant_id = req.get("applicant_id")

                applicant = session.query(Applicant).filter(
                    Applicant.id == applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant not found.")

                if not req.get("first_name"):
                    raise falcon.HTTPNotFound(title="Error", description="First name is a required field.")

                if not req.get("last_name"):
                    raise falcon.HTTPNotFound(title="Error", description="Lat name is a required field.")

                if not req.get("type"):
                    raise falcon.HTTPNotFound(title="Error", description="Type of member is a required field.")

                if not req.get("relation_to_main_member"):
                    raise falcon.HTTPNotFound(title="Error", description="Relationship to main member is a required field.")

                if not req.get("date_joined"):
                    raise falcon.HTTPNotFound(title="Error", description="Date joined is a required field.")

                if req.get("id_number"):
                    applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
                    applicant_ids = [applicant.id for applicant in applicants]
                    id_number = session.query(MainMember).filter(
                        MainMember.id_number == req.get("id_number"),
                        MainMember.applicant_id.in_(applicant_ids),
                        MainMember.state.in_((MainMember.STATE_ACTIVE, MainMember.STATE_ARCHIVED))
                    ).first()

                    if not id_number:
                        applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
                        applicant_ids = [applicant.id for applicant in applicants]
                        id_number = session.query(ExtendedMember).filter(
                            ExtendedMember.id_number == req.get("id_number"),
                            ExtendedMember.state.in_((ExtendedMember.STATE_ACTIVE, ExtendedMember.STATE_ARCHIVED)),
                            ExtendedMember.applicant_id.in_(applicant_ids)
                        ).first()

                    if id_number:
                        raise falcon.HTTPBadRequest(title="Error", description="ID number already exists for either main member or extended member.")

                date_of_birth = self.get_date_of_birth(req.get("date_of_birth"), req.get("id_number"))
                date_joined = self.get_date_joined(req.get("date_joined"))

                extended_member = ExtendedMember(
                    first_name = req.get("first_name"),
                    last_name = req.get("last_name"),
                    number = req.get("number"),
                    date_of_birth = date_of_birth,
                    type = req.get("type"),
                    id_number = req.get("id_number"),
                    relation_to_main_member = req.get("relation_to_main_member"),
                    applicant_id = applicant.id,
                    date_joined = date_joined,
                    waiting_period = req.get("waiting_period", 0),
                    state=ExtendedMember.STATE_ACTIVE,
                    created_at = datetime.now(),
                    modified_at = datetime.now()
                )
                plan = applicant.plan

                if extended_member:
                    if extended_member.type == 4:
                        if not plan.spouse:
                            raise falcon.HTTPBadRequest(title="Error", description="This plan does not have a spouse.")

                        if plan.spouse <= len([member for member in applicant.extended_members if member.type == 4 and member.state == 1]):
                            raise falcon.HTTPBadRequest(title="Error", description="Limit for number of spouse members has been reached.")
                    elif extended_member.type == 1:
                        if not plan.beneficiaries:
                            raise falcon.HTTPBadRequest(title="Error", description="This plan does not have dependants.")

                        if plan.beneficiaries <= len([member for member in applicant.extended_members if member.type == 1 and member.state == 1]):
                            raise falcon.HTTPBadRequest(title="Error", description="Limit for number of dependant members has been reached.")
                    elif extended_member.type == 2:
                        if not plan.extended_members:
                            raise falcon.HTTPBadRequest(title="Error", description="This plan does not have extended-members.")

                        if plan.extended_members <= len([member for member in applicant.extended_members if member.type == 2 and member.state == 1]):
                            raise falcon.HTTPBadRequest(title="Error", description="Limit for number of extended-member members has been reached.")
                    elif extended_member.type == 3:
                        if not plan.additional_extended_members:
                            raise falcon.HTTPBadRequest(title="Error", description="This plan does not have additional-extended-members.")

                        if plan.additional_extended_members <= len([member for member in applicant.extended_members if member.type == 3 and member.state == 1]):
                            raise falcon.HTTPBadRequest(title="Error", description="Limit for number of additional-extended-member members has been reached.")

                member_type = extended_member.type
                min_age_limit = 0
                max_age_limit = 120

                if member_type == 4:
                    min_age_limit = plan.spouse_minimum_age
                    max_age_limit = plan.spouse_maximum_age
                elif member_type == 1:
                    min_age_limit = plan.dependant_minimum_age
                    max_age_limit = plan.dependant_maximum_age
                elif member_type == 2:
                    min_age_limit = plan.extended_minimum_age
                    max_age_limit = plan.extended_maximum_age
                elif member_type == 3:
                    min_age_limit = plan.additional_extended_minimum_age
                    max_age_limit = plan.additional_extended_maximum_age

                if not date_of_birth:
                    if int(id_number[0:2]) > 21:
                        number = '19{}'.format(id_number[0:2])
                    else:
                        number = '20{}'.format(id_number[0:2])
                    date_of_birth = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
                dob = datetime.strptime(self.get_date_of_birth(date_of_birth), "%Y-%m-%d").date()
                now = datetime.now().date()

                age = relativedelta(now, dob)

                years = "{}".format(age.years)

                if max_age_limit and int(max_age_limit):
                    if len(years) > 2 and int(years[2:4]) > int(max_age_limit):
                        extended_member.age_limit_exceeded = True
                    elif int(years) > int(max_age_limit):
                        extended_member.age_limit_exceeded = True

                if min_age_limit and int(min_age_limit):
                    if len(years) > 2 and int(years[2:4]) < int(min_age_limit):
                        extended_member.age_limit_exceeded = True
                    elif int(years) < int(min_age_limit):
                        extended_member.age_limit_exceeded = True

                applicant.extended_members.append(extended_member)
                extended_member.save(session)
                old_file = applicant.document
                update_certificate(applicant)

                if old_file and os.path.exists(old_file):
                    os.remove(old_file)

                resp.body = json.dumps(extended_member.to_dict(), default=str)

        except Exception as e:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise e


class ExtendedMemberCheckAgeLimitEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def get_date_of_birth(self, date_of_birth=None, id_number=None):
        current_year = datetime.now().year
        year_string = str(current_year)[2:]
        century = 19
        if date_of_birth:
            return date_of_birth.replace('T', " ")[:10]
        if id_number:
            if 0 <= int(id_number[:2]) <= int(year_string):
                century = 20
            return '{}{}-{}-{}'.format(century,id_number[:2], id_number[2:4], id_number[4:-6])[:10]

    def on_get(self, req, resp, id):

        with db.no_transaction() as session:
            age_limit_exceeded = False
            id_number = None
            date_of_birth = None
            plan = None
            max_age_limit = None
            min_age_limit = None

            if "id_number" in req.params:
                id_number = req.params.pop("id_number")

            if "date_of_birth" in req.params:
                date_of_birth = req.params.pop("date_of_birth")

            if "type" in req.params:
                member_type = req.params.pop("type")

            if not member_type:
                raise falcon.HTTPBadRequest(title="Error", description="extended member type is required.")

            applicant = session.query(Applicant).get(id)

            if not applicant:
                raise falcon.HTTPBadRequest(title="Applicant not found", description="Applicant does not exist.")

            plan = applicant.plan

            if not id_number and not date_of_birth:
                raise falcon.HTTPBadRequest(title="Error", description="ID number or date of birth field must be entered.")

            if member_type == '4':
                if not plan.spouse:
                    raise falcon.HTTPBadRequest(title="Error", description="This plan does not have a spouse.")
            elif member_type == '1':
                if not plan.beneficiaries:
                    raise falcon.HTTPBadRequest(title="Error", description="This plan does not have dependants.")
            elif member_type == '2':
                if not plan.extended_members:
                    raise falcon.HTTPBadRequest(title="Error", description="This plan does not have extended-members.")
            elif member_type == '3':
                if not plan.additional_extended_members:
                    raise falcon.HTTPBadRequest(title="Error", description="This plan does not have additional-extended-members.")

            if member_type == '4':
                min_age_limit = plan.spouse_minimum_age
                max_age_limit = plan.spouse_maximum_age
            elif member_type == '1':
                min_age_limit = plan.dependant_minimum_age
                max_age_limit = plan.dependant_maximum_age
            elif member_type == '2':
                min_age_limit = plan.extended_minimum_age
                max_age_limit = plan.extended_maximum_age
            elif member_type == '3':
                min_age_limit = plan.additional_extended_minimum_age
                max_age_limit = plan.additional_extended_maximum_age

            if not date_of_birth:
                if int(id_number[0:2]) > 21:
                    number = '19{}'.format(id_number[0:2])
                else:
                    number = '20{}'.format(id_number[0:2])
                date_of_birth = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
            dob = datetime.strptime(self.get_date_of_birth(date_of_birth, id_number), "%Y-%m-%d").date()
            now = datetime.now().date()

            age = relativedelta(now, dob)

            years = "{}".format(age.years)

            if max_age_limit and int(max_age_limit):
                if len(years) > 2 and int(years[2:4]) > int(max_age_limit):
                    age_limit_exceeded = True
                elif int(years) > int(max_age_limit):
                    age_limit_exceeded = True

            if min_age_limit and int(min_age_limit):
                if len(years) > 2 and int(years[2:4]) < int(min_age_limit):
                    age_limit_exceeded = True
                elif int(years) < int(min_age_limit):
                    age_limit_exceeded = True

            if age_limit_exceeded:
                resp.body = json.dumps({'result': 'Age limit exceeded!'})
            else:
                resp.body = json.dumps({'result': 'OK!'})


class ExtendedMemberPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def get_date_of_birth(self, date_of_birth=None, id_number=None):
        current_year = datetime.now().year
        year_string = str(current_year)[2:]
        century = 19
        if id_number:
            if 0 <= int(id_number[:2]) <= int(year_string):
                century = 20
            return '{}{}-{}-{}'.format(century,id_number[:2], id_number[2:4], id_number[4:-6])[:10]
        if date_of_birth:
            return date_of_birth.replace('T', " ")[:10]

    def get_date_joined(self, date_joined):
        return date_joined.replace('T', " ")[:10]

    def on_put(self, req, resp, id):
        req = json.load(req.bounded_stream)

        with db.transaction() as session:
            applicant_id = req.get("applicant_id")
            id_number = None

            applicant = session.query(Applicant).filter(
                Applicant.id == applicant_id).one_or_none()

            if not applicant:
                raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")

            if not req.get("first_name"):
                raise falcon.HTTPNotFound(title="Error", description="First name is a required field.")

            if not req.get("last_name"):
                raise falcon.HTTPNotFound(title="Error", description="Lat name is a required field.")

            if not req.get("type"):
                raise falcon.HTTPNotFound(title="Error", description="Type of member is a required field.")

            if not req.get("relation_to_main_member"):
                raise falcon.HTTPNotFound(title="Error", description="Relationship to main member is a required field.")

            if not req.get("date_joined"):
                raise falcon.HTTPNotFound(title="Error", description="Date joined is a required field.")

            if req.get("id_number"):
                id_number = session.query(MainMember).filter(MainMember.id_number == req.get("id_number"), MainMember.parlour_id == applicant.parlour_id).first()

            if req.get("id_number") and not id_number:
                applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
                applicant_ids = [applicant.id for applicant in applicants]

                id_number = session.query(MainMember).filter(
                    MainMember.id_number == req.get("id_number"),
                    MainMember.applicant_id.in_(applicant_ids),
                    MainMember.state.in_((MainMember.STATE_ACTIVE, MainMember.STATE_ARCHIVED))
                ).first()

                if not id_number:
                    applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
                    applicant_ids = [applicant.id for applicant in applicants]
                    id_number = session.query(ExtendedMember).filter(
                        ExtendedMember.id_number == req.get("id_number"),
                        ExtendedMember.id != id,
                        ExtendedMember.state.in_((ExtendedMember.STATE_ACTIVE, ExtendedMember.STATE_ARCHIVED)),
                        ExtendedMember.applicant_id.in_(applicant_ids)
                    ).first()

            if id_number:
                raise falcon.HTTPBadRequest(title="Error", description="ID number already exists for either main member or extended member.")

            plan = applicant.plan
            extended_member = session.query(ExtendedMember).filter(
                ExtendedMember.id == id,
                ExtendedMember.applicant_id == applicant.id,
                ExtendedMember.state == ExtendedMember.STATE_ACTIVE).first()

            if not extended_member:
                raise falcon.HTTPNotFound(title="ExtenedMember not found", description="Could not find Applicant with given ID.")

            try:
                date_of_birth = self.get_date_of_birth(req.get("date_of_birth"), req.get("id_number"))
                date_joined = self.get_date_joined(req.get("date_joined"))
                old_type = extended_member.type
                extended_member.first_name = req.get("first_name")
                extended_member.last_name = req.get("last_name")
                extended_member.number = req.get("number")
                extended_member.date_of_birth = date_of_birth
                extended_member.type = req.get("type")
                extended_member.id_number = req.get("id_number")
                extended_member.waiting_period = req.get("waiting_period", 0)
                extended_member.relation_to_main_member = req.get("relation_to_main_member")
                extended_member.applicant_id = applicant.id
                extended_member.date_joined = date_joined
                extended_member.modified_at = datetime.now()

                plan = applicant.plan
                if extended_member.type == 4 and extended_member.type != old_type:
                    if not plan.spouse:
                        raise falcon.HTTPBadRequest(title="Error", description="This plan does not have a spouse.")

                    if plan.spouse <= len([member for member in applicant.extended_members if member.type == 4 and member.state == 1]):
                        raise falcon.HTTPBadRequest(title="Error", description="Limit for number of spouse members has been reached.")
                elif extended_member.type == 1 and extended_member.type != old_type:
                    if not plan.beneficiaries:
                        raise falcon.HTTPBadRequest(title="Error", description="This plan does not have dependants.")

                    if plan.beneficiaries <= len([member for member in applicant.extended_members if member.type == 1 and member.state == 1]):
                        raise falcon.HTTPBadRequest(title="Error", description="Limit for number of dependant members has been reached.")
                elif extended_member.type == 2 and extended_member.type != old_type:
                    if not plan.extended_members:
                        raise falcon.HTTPBadRequest(title="Error", description="This plan does not have extended-members.")

                    if plan.extended_members <= len([member for member in applicant.extended_members if member.type == 2 and member.state == 1]):
                        raise falcon.HTTPBadRequest(title="Error", description="Limit for number of extended-member members has been reached.")
                elif extended_member.type == 3 and extended_member.type != old_type:
                    if not plan.additional_extended_members:
                        raise falcon.HTTPBadRequest(title="Error", description="This plan does not have additional-extended-members.")

                    if plan.additional_extended_members <= len([member for member in applicant.extended_members if member.type == 3 and member.state == 1]):
                        raise falcon.HTTPBadRequest(title="Error", description="Limit for number of additional-extended-member members has been reached.")

                member_type = extended_member.type
                min_age_limit = 0
                max_age_limit = 120

                if member_type == 4:
                    min_age_limit = plan.spouse_minimum_age
                    max_age_limit = plan.spouse_maximum_age
                elif member_type == 1:
                    min_age_limit = plan.dependant_minimum_age
                    max_age_limit = plan.dependant_maximum_age
                elif member_type == 2:
                    min_age_limit = plan.extended_minimum_age
                    max_age_limit = plan.extended_maximum_age
                elif member_type == 3:
                    min_age_limit = plan.additional_extended_minimum_age
                    max_age_limit = plan.additional_extended_maximum_age

                if not date_of_birth:
                    if int(id_number[0:2]) > 21:
                        number = '19{}'.format(id_number[0:2])
                    else:
                        number = '20{}'.format(id_number[0:2])
                    date_of_birth = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
                dob = datetime.strptime(self.get_date_of_birth(date_of_birth), "%Y-%m-%d").date()
                now = datetime.now().date()

                age = relativedelta(now, dob)

                years = "{}".format(age.years)

                if max_age_limit and int(max_age_limit):
                    if len(years) > 2 and int(years[2:4]) > int(max_age_limit):
                        extended_member.age_limit_exceeded = True
                    elif int(years) > int(max_age_limit):
                        extended_member.age_limit_exceeded = True

                if min_age_limit and int(min_age_limit):
                    if len(years) > 2 and int(years[2:4]) < int(min_age_limit):
                        extended_member.age_limit_exceeded = True
                    elif int(years) < int(min_age_limit):
                        extended_member.age_limit_exceeded = True

                extended_member.save(session)
                old_file = applicant.document
                update_certificate(applicant)

                if old_file and os.path.exists(old_file):
                    os.remove(old_file)

                resp.body = json.dumps(applicant.to_dict(), default=str)
            except Exception as e:
                logger.exception(
                    "Error, experienced error while creating Applicant.")
                raise e


class ExtededMemberDeleteEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                extended_member = session.query(ExtendedMember).get(id)

                if extended_member is None:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant Not Found")
                if extended_member.is_deleted:
                    falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not exist.")

                extended_member.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Applicant with ID {}.".format(id))


class MainMemberPromoteEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def get_date_joined(self, date_joined):
        return date_joined.replace('T', " ")[:10]

    def on_post(self, req, resp, id):

        req = json.load(req.bounded_stream)

        with db.transaction() as session:
            extended_member = session.query(ExtendedMember).filter(ExtendedMember.id == id).one()

            applicant = session.query(Applicant).filter(
                Applicant.id == extended_member.applicant_id).one_or_none()

            if not applicant:
                raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not exist.")

            if not req.get("first_name"):
                raise falcon.HTTPNotFound(title="Error", description="First name is a required field.")

            if not req.get("last_name"):
                raise falcon.HTTPNotFound(title="Error", description="Lat name is a required field.")

            if not req.get("type"):
                raise falcon.HTTPNotFound(title="Error", description="Type of member is a required field.")

            if not req.get("relation_to_main_member"):
                raise falcon.HTTPNotFound(title="Error", description="Relationship to main member is a required field.")

            if not req.get("date_joined"):
                raise falcon.HTTPNotFound(title="Error", description="Date joined is a required field.")

            if not req.get("id_number"):
                raise falcon.HTTPNotFound(title="Error", description="ID number required when promoting to main member.")

            if not req.get("number"):
                raise falcon.HTTPNotFound(title="Error", description="Contact number required when promoting to main member.")

            plan = session.query(Plan).filter(
                Plan.id == applicant.plan_id,
                Plan.state == Plan.STATE_ACTIVE).one_or_none()

            if not plan:
                raise falcon.HTTPBadRequest(title="Error", description="Plan does not exist.")

            try:
                # main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id).one_or_none()
                main_member = update_deceased_member(session, applicant, extended_member)

                min_age_limit = plan.member_minimum_age
                max_age_limit = plan.member_maximum_age

                id_number = main_member.id_number
                if int(id_number[0:2]) > 21:
                    number = '19{}'.format(id_number[0:2])
                else:
                    number = '20{}'.format(id_number[0:2])
                dob = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
                # dob = main_member.date_of_birth
                dob = datetime.strptime(dob, "%Y-%m-%d")
                now = datetime.now()

                age = relativedelta(now, dob)

                years = "{}".format(age.years)
                try:
                    if max_age_limit and len(years) > 2 and int(years[2:4]) > max_age_limit:
                        main_member.age_limit_exceeded = True
                    elif max_age_limit and  int(years) > max_age_limit:
                        main_member.age_limit_exceeded = True
                except:
                    pass

                try:
                    if min_age_limit and len(years) > 2 and int(years[2:4]) < min_age_limit:
                        main_member.age_limit_exceeded = True
                    elif min_age_limit and int(years) < min_age_limit:
                        main_member.age_limit_exceeded = True
                except:
                    pass
                main_member.save(session)

                applicant = update_certificate(applicant)

                resp.body = json.dumps(main_member.to_dict(), default=str)
            except MultipleResultsFound as e:
                raise falcon.HTTPBadRequest(title="Error", description="More than one member exists for this applicant")
            except NoResultFound as e:
                raise falcon.HTTPBadRequest(title="Error", description="No member exists for this applicant")
            except Exception as e:
                logger.exception(
                    "Error, experienced error while creating Applicant.")
                raise e


def update_deceased_member(session, applicant, extended_member):
    extended_members = session.query(ExtendedMember).filter(ExtendedMember.applicant_id == applicant.id).all()

    new_applicant = Applicant(
        policy_num=applicant.policy_num,
        address=applicant.address,
        status='unpaid',
        plan_id=applicant.plan_id,
        consultant_id=applicant.consultant_id,
        parlour_id=applicant.parlour_id,
        old_url=False,
        date=datetime.now(),
        state=Applicant.STATE_ACTIVE,
        modified_at=datetime.now(),
        created_at=datetime.now()
    )

    new_applicant.save(session)
    date_joined = extended_member.date_joined
    main_member = MainMember(
        first_name=extended_member.first_name,
        last_name=extended_member.last_name,
        id_number=extended_member.id_number,
        contact=extended_member.number,
        date_of_birth=extended_member.date_of_birth,
        parlour_id=applicant.parlour_id,
        date_joined=date_joined,
        state=MainMember.STATE_ACTIVE,
        applicant_id=new_applicant.id,
        modified_at=datetime.now(),
        created_at=datetime.now()
    )

    main_member.save(session)
    for x in extended_members:
        if x.id == extended_member.id:
            x.make_deleted()
        else:
            x.applicant_id = new_applicant.id
            x.is_main_member_deceased = False
    session.commit()
    update_certificate(new_applicant)
    return main_member


def update_certificate(applicant):
    with db.transaction() as session:
        parlour = session.query(Parlour).filter(Parlour.id == applicant.parlour.id).one_or_none()
        plan = session.query(Plan).filter(Plan.id == applicant.plan.id).one_or_none()
        main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id, MainMember.state == MainMember.STATE_ACTIVE).first()

        if main_member:
            extended_members = session.query(ExtendedMember).filter(
                ExtendedMember.applicant_id == applicant.id,
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
                canvas.set_physical_address(applicant.address if applicant.address else '')

                for extended_member in extended_members:
                    canvas.add_other_members(extended_member)

                if plan.benefits:
                    canvas.set_benefits(plan.benefits)
                canvas.save()
                applicant.document = canvas.get_file_path()

            except Exception as e:
                logger.exception("Error, experienced an error while creating certificate.")
                print(e)

    return applicant


def get_date_of_birth(id_number=None):
    current_year = datetime.now().year
    year_string = str(current_year)[2:]
    century = 19
    if 0 <= int(id_number[:2]) <= int(year_string):
        century = 20
    return '{}{}/{}/{}'.format(century,id_number[:2], id_number[2:4], id_number[4:6])[:10]


def bulk_insert_extended_members(csv_data, error_data, applicant_id, session):
    ext_data = []
    ext_data.append(csv_data)

    for data in ext_data:
        applicant = session.query(Applicant).filter(
            Applicant.id == applicant_id,
            Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

        if not applicant:
            error_data.append({'data': data, 'error': "Applicant not found."})
            continue

        if not data[0]:
            error_data.append({'data': data, 'error': "First name is a required field."})
            continue

        if not data[1]:
            error_data.append({'data': data, 'error': "Last name is a required field."})
            continue

        if not data[2]:
            error_data.append({'data': data, 'error': "ID number/dob is a required field."})
            continue

        if not data[8]:
            error_data.append({'data': data, 'error': "Type of member is a required field."})
            continue

        if not data[9]:
            error_data.append({'data': data, 'error': "Relationship to main member is a required field."})
            continue

        if not data[4]:
            error_data.append({'data': data, 'error': "Date joined is a required field."})
            continue

        id_check = '{}'.format(data[2])
        id_number = None
        if not id_check:
            error_data.append({'data': data, 'error': "ID Number is a required field."})
            continue
        if len(id_check) == 13:
            za_validation = SouthAfricanIdentityValidate(id_check)
            valid = za_validation.validate()
            if not valid:
                error_data.append({'data': data, 'error': "Incorrect id_number entered."})
                continue
        if id_check and len(id_check) == 13:
            applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
            applicant_ids = [applicant.id for applicant in applicants]
            id_number = session.query(MainMember).filter(
                MainMember.id_number == id_check,
                MainMember.applicant_id.in_(applicant_ids),
                MainMember.state.in_((MainMember.STATE_ACTIVE, MainMember.STATE_ARCHIVED))
            ).first()

            if not id_number:
                applicants = session.query(Applicant).filter(Applicant.parlour_id == applicant.parlour_id).all()
                applicant_ids = [applicant.id for applicant in applicants]
                id_number = session.query(ExtendedMember).filter(
                    ExtendedMember.id_number == id_check,
                    ExtendedMember.state.in_((ExtendedMember.STATE_ACTIVE, ExtendedMember.STATE_ARCHIVED)),
                    ExtendedMember.applicant_id.in_(applicant_ids)
                ).first()

            if id_number:
                error_data.append({'data': data, 'error': "ID number already exists for either main member or extended member."})
                continue

        if len(id_check) < 13:
            try:
                try:
                    date_of_birth = datetime.strptime(id_check, "%d/%m/%Y")
                except ValueError:
                    date_of_birth = datetime.strptime(id_check, "%d-%m-%Y")
            except ValueError:
                try:
                    date_of_birth = datetime.strptime(id_check, "%Y/%m/%d")
                except ValueError:
                    date_of_birth = datetime.strptime(id_check, "%Y-%m-%d")
            except:
                error_data.append({'data': data, 'error': 'Incorrect date format on date of birth'})
                continue
        else:
            dob = get_date_of_birth(id_check)
            try:
                date_of_birth = datetime.strptime(dob, "%d/%m/%Y")
            except ValueError:
                try:
                    date_of_birth = datetime.strptime(dob, "%Y/%m/%d")
                except ValueError:
                    error_data.append({'data': data, 'error': 'Incorrect date format on date of birth or id_number'})
                    continue

        date_joined = data[4]
        member_type = '_'.join('{}'.format(data[8]).lower().split(' '))
        member_relation = '_'.join('{}'.format(data[9]).lower().split(' '))
        member_type_value = ExtendedMember.text_type(member_type) if ExtendedMember.text_type(member_type) != 'Undefined' else None
        member_relation_value = ExtendedMember.text_relation(member_relation)
        if not member_type_value:
            error_data.append({'data': data, 'error': "Unrecognized member type."})
            continue
        if not member_relation_value:
            error_data.append({'data': data, 'error': "Unrecognized member relation."})
            continue

        extended_member = ExtendedMember(
            first_name = data[0],
            last_name = data[1],
            number = data[3] if len(str(data[3])) == 10 else '0{}'.format(data[3]),
            date_of_birth = date_of_birth,
            type = member_type_value,
            id_number = id_number,
            relation_to_main_member = member_relation_value,
            applicant_id = applicant.id,
            date_joined = date_joined,
            waiting_period=data[5] if data[5] else 0,
            state=ExtendedMember.STATE_ACTIVE,
            created_at = datetime.now(),
            modified_at = datetime.now()
        )
        plan = applicant.plan

        if extended_member:
            if extended_member.type == 4:
                if not plan.spouse:
                    error_data.append({'data': data, 'error': "This plan does not have a spouse."})
                    continue

                if plan.spouse <= len([member for member in applicant.extended_members if member.type == 4 and member.state == 1]):
                    error_data.append({'data': data, 'error': "Limit for number of spouse members has been reached."})
                    continue

            elif extended_member.type == 1:
                if not plan.beneficiaries:
                    error_data.append({'data': data, 'error': "This plan does not have dependants."})
                    continue

                if plan.beneficiaries <= len([member for member in applicant.extended_members if member.type == 1 and member.state == 1]):
                    error_data.append({'data': data, 'error': "Limit for number of dependant members has been reached."})
                    continue

            elif extended_member.type == 2:
                if not plan.extended_members:
                    error_data.append({'data': data, 'error': "This plan does not have extended-members."})
                    continue

                if plan.extended_members <= len([member for member in applicant.extended_members if member.type == 2 and member.state == 1]):
                    error_data.append({'data': data, 'error': "Limit for number of extended-member members has been reached."})
                    continue

            elif extended_member.type == 3:
                if not plan.additional_extended_members:
                    error_data.append({'data': data, 'error': "This plan does not have additional-extended-members."})
                    continue

                if plan.additional_extended_members <= len([member for member in applicant.extended_members if member.type == 3 and member.state == 1]):
                    error_data.append({'data': data, 'error': "Limit for number of additional-extended-member members has been reached."})
                    continue

        member_type = extended_member.type
        min_age_limit = 0
        max_age_limit = 120

        if member_type == 4:
            min_age_limit = plan.spouse_minimum_age
            max_age_limit = plan.spouse_maximum_age
        elif member_type == 1:
            min_age_limit = plan.dependant_minimum_age
            max_age_limit = plan.dependant_maximum_age
        elif member_type == 2:
            min_age_limit = plan.extended_minimum_age
            max_age_limit = plan.extended_maximum_age
        elif member_type == 3:
            min_age_limit = plan.additional_extended_minimum_age
            max_age_limit = plan.additional_extended_maximum_age

        now = datetime.now().date()
        age = relativedelta(now, date_of_birth)

        years = "{}".format(age.years)

        if max_age_limit and int(max_age_limit):
            if len(years) > 2 and int(years[2:4]) > int(max_age_limit):
                extended_member.age_limit_exceeded = True
            elif int(years) > int(max_age_limit):
                extended_member.age_limit_exceeded = True

        if min_age_limit and int(min_age_limit):
            if len(years) > 2 and int(years[2:4]) < int(min_age_limit):
                extended_member.age_limit_exceeded = True
            elif int(years) < int(min_age_limit):
                extended_member.age_limit_exceeded = True

        applicant.extended_members.append(extended_member)
        extended_member.save(session)
        old_file = applicant.document
        update_certificate(applicant)

        if old_file and os.path.exists(old_file):
            os.remove(old_file)
    return error_data