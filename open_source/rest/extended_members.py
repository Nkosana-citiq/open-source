from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from open_source.core.main_members import MainMember
from sqlalchemy.orm import relation

from open_source.core.extended_members import ExtendedMember
from open_source.core.applicants import Applicant
from open_source.core.certificate import Certificate
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from falcon_cors import CORS

import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant

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
                    Applicant.state == Applicant.STATE_ACTIVE,
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
        req = json.loads(req.stream.read().decode('utf-8'))
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
        req = json.loads(req.stream.read().decode('utf-8'))

        try:
            with db.transaction() as session:
                applicant_id = req.get("applicant_id")

                applicant = session.query(Applicant).filter(
                    Applicant.id == applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")

                if req.get("id_number"):
                    id_number = session.query(ExtendedMember).join(MainMember, applicant_id == ExtendedMember.applicant_id).filter(
                        ExtendedMember.id_number == req.get("id_number")).first()

                    if id_number:
                        raise falcon.HTTPBadRequest(title="Error", description="ID number already exists.")

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
                    state=ExtendedMember.STATE_ACTIVE,
                    created_at = datetime.now(),
                    modified_at = datetime.now()
                )
                plan = applicant.plan
                
                plan = applicant.plan
                if extended_member:
                    if extended_member.type == 0:
                        min_age_limit = plan.spouse_minimum_age
                        max_age_limit = plan.spouse_maximum_age
                    elif extended_member.type == 1:
                        min_age_limit = plan.dependant_minimum_age
                        max_age_limit = plan.dependant_maximum_age
                    elif extended_member.type == 2:
                        min_age_limit = plan.extended_minimum_age
                        max_age_limit = plan.extended_maximum_age
                    elif extended_member.type == 3:
                        min_age_limit = plan.additional_extended_minimum_age
                        max_age_limit = plan.additional_extended_maximum_age

                    dob = extended_member.date_of_birth
                    if not dob:
                        id_number = extended_member.id_number
                        if int(id_number[0:2]) > 21:
                            number = '19{}'.format(id_number[0:2])
                        else:
                            number = '20{}'.format(id_number[0:2])
                        id_number = extended_member.id_number
                        dob = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
                    dob = datetime.strptime(dob, "%Y-%m-%d")
                    now = datetime.now()

                    age = relativedelta(now, dob)

                    years = "{}".format(age.years)

                    if max_age_limit:
                        if len(years) > 2 and int(years[2:4]) > max_age_limit:
                            raise falcon.HTTPBadRequest(
                                title="Error",
                                description="Age Limit exceeded.")
                        elif int(years) > max_age_limit:
                            raise falcon.HTTPBadRequest(
                                title="Error",
                                description="Age Limit exceeded.")

                    if min_age_limit:
                        if len(years) > 2 and int(years[2:4]) < min_age_limit:
                            raise falcon.HTTPBadRequest(
                                title="Error",
                                description="Age not within required age limit.")
                        elif int(years) < min_age_limit:
                            raise falcon.HTTPBadRequest(
                                title="Error",
                                description="Age not within required age limit.")

                extended_member.save(session)
                update_certificate(applicant)
                resp.body = json.dumps(extended_member.to_dict(), default=str)

        except Exception as e:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise e


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
        if date_of_birth:
            return date_of_birth.replace('T', " ")[:10]
        if id_number:
            if 0 <= int(id_number[:2]) <= int(year_string):
                century = 20
            return '{}{}-{}-{}'.format(century,id_number[:2], id_number[2:4], id_number[4:-6])[:10]

    def get_date_joined(self, date_joined):
        return date_joined.replace('T', " ")[:10]

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                applicant_id = req.get("applicant_id")

                applicant = session.query(Applicant).filter(
                    Applicant.id == applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")
                plan = applicant.plan
                extended_member = session.query(ExtendedMember).filter(
                    ExtendedMember.id == id,
                    ExtendedMember.applicant_id == applicant.id,
                    ExtendedMember.state == ExtendedMember.STATE_ACTIVE).first()

                if not extended_member:
                    raise falcon.HTTPNotFound(title="ExtenedMember not found", description="Could not find Applicant with given ID.")

                date_of_birth = self.get_date_of_birth(req.get("date_of_birth"), req.get("id_number"))
                date_joined = self.get_date_joined(req.get("date_joined"))

                extended_member.first_name = req.get("first_name")
                extended_member.last_name = req.get("last_name")
                extended_member.number = req.get("number")
                extended_member.date_of_birth = date_of_birth
                extended_member.type = req.get("type")
                extended_member.id_number = req.get("id_number")
                extended_member.relation_to_main_member = req.get("relation_to_main_member")
                extended_member.applicant_id = applicant.id
                extended_member.date_joined = date_joined
                extended_member.modified_at = datetime.now()

                plan = applicant.plan
                if extended_member:
                    if extended_member.type == 0:
                        min_age_limit = plan.spouse_minimum_age
                        max_age_limit = plan.spouse_maximum_age
                    elif extended_member.type == 1:
                        min_age_limit = plan.dependant_minimum_age
                        max_age_limit = plan.dependant_maximum_age
                    elif extended_member.type == 2:
                        min_age_limit = plan.extended_minimum_age
                        max_age_limit = plan.extended_maximum_age
                    elif extended_member.type == 3:
                        min_age_limit = plan.additional_extended_minimum_age
                        max_age_limit = plan.additional_extended_maximum_age

                    dob = extended_member.date_of_birth
                    dob = datetime.strptime(dob, "%Y-%m-%d")
                    now = datetime.now()

                    age = relativedelta(now, dob)

                    years = "{}".format(age.years)

                    if len(years) > 2 and int(years[2:4]) > max_age_limit:
                        raise falcon.HTTPBadRequest(
                            title="Error", 
                            description="Age Limit exceeded.")
                    elif int(years) > max_age_limit:
                        raise falcon.HTTPBadRequest(
                            title="Error", 
                            description="Age Limit exceeded.")

                    if len(years) > 2 and int(years[2:4]) < min_age_limit:
                        raise falcon.HTTPBadRequest(
                            title="Error", 
                            description="Age not within required age limit.")
                    elif int(years) < min_age_limit:
                        raise falcon.HTTPBadRequest(
                            title="Error", 
                            description="Age not within required age limit.")

                extended_member.save(session)
                update_certificate(applicant)
                resp.body = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                title="Error", 
                description="Processing Failed. experienced error while creating Applicant.")


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


def update_certificate(applicant):
    with db.no_transaction() as session:
        parlour = session.query(Parlour).filter(Parlour.id == applicant.parlour.id).one_or_none()
        plan = session.query(Plan).filter(Plan.id == applicant.plan.id).one_or_none()
        main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id, MainMember.state == MainMember.STATE_ACTIVE).one_or_none()
        spouse = session.query(ExtendedMember).filter(
            ExtendedMember.applicant_id == applicant.id,
            ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
            ExtendedMember.type == ExtendedMember.TYPE_SPOUSE).all()
        dependants = session.query(ExtendedMember).filter(
            ExtendedMember.applicant_id == applicant.id,
            ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
            ExtendedMember.type == ExtendedMember.TYPE_DEPENDANT).all()
        extended_member = session.query(ExtendedMember).filter(
            ExtendedMember.applicant_id == applicant.id,
            ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
            ExtendedMember.type == ExtendedMember.TYPE_EXTENDED_MEMBER).all()
        additional_extended_member = session.query(ExtendedMember).filter(
            ExtendedMember.applicant_id == applicant.id,
            ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
            ExtendedMember.type == ExtendedMember.TYPE_ADDITIONAL_EXTENDED_MEMBER).all()

        try:
            canvas = Certificate(parlour.parlourname.strip())
            canvas.set_title(parlour.parlourname)
            canvas.set_address(parlour.address if parlour.address else '')
            canvas.set_contact(parlour.number)
            canvas.set_email(parlour.email)
            canvas.membership_certificate()
            canvas.set_member("Main Member")
            canvas.set_name(' '.join([main_member.first_name, main_member.last_name]))
            canvas.set_id_number(main_member.id_number)
            canvas.set_date_joined(main_member.date_joined)
            canvas.set_member_contact(main_member.contact)
            canvas.set_current_plan(plan.plan)
            canvas.set_current_premium(plan.premium)
            canvas.set_physical_address(main_member.applicant.address if main_member.applicant.address else '')
            count = 0

            for s in spouse:
                canvas.add_other_members(s)
                count += 1
                if count == 4:
                    canvas.showPage()
                    canvas.y_position = 60

            for d in dependants:
                canvas.add_other_members(d)
                count += 1
                if count == 4:
                    canvas.showPage()
                    canvas.y_position = 60

            for e in extended_member:
                canvas.add_other_members(e)
                count += 1
                if count == 4:
                    canvas.showPage()
                    canvas.y_position = 60

            for a in additional_extended_member:
                canvas.add_other_members(a)
                count += 1
                if count == 4:
                    canvas.showPage()
                    canvas.y_position = 60

            canvas.set_benefits(plan.benefits)
            canvas.save()
            applicant.document = canvas.get_file_path()

        except Exception as e:
            logger.exception("Error, experienced an error while creating certificate.")
            print(e)
