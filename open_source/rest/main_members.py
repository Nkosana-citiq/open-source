import datetime
from dateutil.relativedelta import relativedelta
from falcon.errors import HTTPBadRequest
from open_source import config
from open_source.core import consultants
from open_source.core import main_members

from open_source.core.consultants import Consultant
from open_source.core.plans import Plan
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import or_
from open_source.core.main_members import MainMember
from open_source.core.extended_members import ExtendedMember
from open_source.rest.extended_members import update_certificate
from open_source.core.parlours import Parlour
from falcon_cors import CORS
from open_source.core.certificate import Certificate

import os
import csv
import uuid
import mimetypes
import falcon
import json
import logging
import pandas as pd
from PyPDF2 import PdfFileReader, PdfFileWriter
import cgi
from open_source import db

from open_source.core.applicants import Applicant

logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

conf = config.get_config()

class MainMemberGetEndpoint:
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
            main_member = session.query(MainMember).filter(
                MainMember.id == id,
                MainMember.state == MainMember.STATE_ACTIVE
            ).first()

            if main_member is None:
                raise falcon.HTTPNotFound(title="Not Found", description="Applicant Not Found")

            resp.body = json.dumps(main_member.to_dict(), default=str)


class MainGetAllParlourEndpoint:
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
                try:
                    status = None
                    search_field = None
                    search_date = None
                    notice = None
                    consultant = None
                    consultants = None
                    parlour_branch = None
                    start_date = None
                    end_date = None

                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "search_string" in req.params:
                        search_field = req.params.pop("search_string")

                    if "search_date" in req.params:
                        search_date = req.params.pop("search_date")

                    if "notice" in req.params:
                        notice = req.params.pop("notice")

                    if "start_date" in req.params:
                        start_date = req.params.pop("start_date")

                    if "end_date" in req.params:
                        end_date = req.params.pop("end_date")

                    if "consultant" in req.params:
                        consultant_id = req.params.pop("consultant")
                        consultant = session.query(Consultant).get(consultant_id)

                    if "branch" in req.params:
                        parlour_branch = req.params.pop("branch")
                        consultants = session.query(Consultant).filter(Consultant.branch == parlour_branch.strip()).all()

                    parlour = session.query(Parlour).filter(
                        Parlour.state == Parlour.STATE_ACTIVE,
                        Parlour.id == id
                    ).one_or_none()

                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if search_date:
                    search = datetime.datetime.strptime(search_date, "%d/%m/%Y")

                    main_members = session.query(MainMember).filter(MainMember.state == MainMember.STATE_ACTIVE, MainMember.parlour_id == parlour.id).all()
                    main_count = len(main_members)
                    main_members = [m for m in main_members if m.date_joined and m.date_joined.year == search.date().year and m.date_joined.month == search.date().month]
                    month_count = len(main_members)

                    resp.body = json.dumps({"original": main_count, "month": month_count, "period": '-'.join([str(search.date().year), str(search.date().month)])}, default=str)
                elif search_field:
                    main_members = session.query(
                        MainMember,
                        Applicant
                    ).join(Applicant, (MainMember.applicant_id==Applicant.id)).filter(
                        MainMember.state == MainMember.STATE_ACTIVE,
                        Applicant.parlour_id == parlour.id,
                        Applicant.status != 'lapsed',
                        or_(
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.last_name.ilike('{}%'.format(search_field)),
                            MainMember.id_number.ilike('{}%'.format(search_field)),
                            Applicant.policy_num.ilike('{}%'.format(search_field))
                        )
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])
                    else:
                        resp.body = json.dumps([main_member[0].to_dict() for main_member in main_members], default=str)
                else:
                    applicants = session.query(Applicant).filter(
                        Applicant.state == Applicant.STATE_ACTIVE,
                        Applicant.status != 'lapsed',
                        Applicant.parlour_id == parlour.id
                    ).order_by(Applicant.id.desc())

                    if consultant:
                        applicants = applicants.filter(Applicant.consultant_id == consultant.id)
                    
                    if consultants:
                        consultant_ids = [consultant.id for consultant in consultants]
                        applicants = applicants.filter(Applicant.consultant_id.in_(consultant_ids))

                    if status:
                        applicants = applicants.filter(Applicant.status == status.lower())

                    applicant_res = [(applicant, applicant.plan) for applicant in applicants.all()]
                    if applicant_res:
                        for applicant in applicant_res:
                            if applicant[0].plan.id == applicant[1].id:
                                max_age_limit = applicant[1].member_maximum_age
                                min_age_limit = applicant[1].member_minimum_age
                                main_member = session.query(MainMember).filter(
                                    MainMember.state == MainMember.STATE_ACTIVE,
                                    MainMember.applicant_id == applicant[0].id
                                ).first()
                                if main_member:
                                    id_number = main_member.id_number
                                    number = int(id_number[0:2])
                                    if number == 0:
                                        number = 2000

                                    dob = datetime.datetime(number, int(id_number[2:4]), int(id_number[4:6]),0,0,0,0)
                                    now = datetime.datetime.now()
                                    age = relativedelta(now, dob)

                                    years = str(age.years)[2:] if str(age.years)[2:].isdigit() else str(age.years)
                                    if int(years) > max_age_limit:
                                        main_member.age_limit_exceeded = True
                                    if int(years) < min_age_limit:
                                        main_member.age_limit_exceeded = True
                                        session.commit()
                    applicant_ids = [applicant.id for applicant in applicants.all()]
                    main_members = session.query(MainMember).filter(
                        MainMember.state == MainMember.STATE_ACTIVE,
                        MainMember.applicant_id.in_(applicant_ids)
                    )

                    if start_date:
                        main_members = main_members.filter(
                            MainMember.created_at >= start_date
                        )

                    if end_date:
                        main_members = main_members.filter(
                            MainMember.created_at <= end_date
                        )
                    if not main_members.all():
                        resp.body = json.dumps([])
                    else:
                        resp.body = json.dumps([main_member.to_dict() for main_member in main_members.all()], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class MainGetAllConsultantEndpoint:
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
                try:
                    status = None
                    search_field = None
                    notice = None

                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "search_string" in req.params:
                        search_field = req.params.pop("search_string")

                    if "notice" in req.params:
                        notice = req.params.pop("notice")

                    consultant = session.query(Consultant).filter(
                        Consultant.state == Consultant.STATE_ACTIVE,
                        Consultant.id == id
                    ).one_or_none()

                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if search_field:
                    main_members = session.query(
                        MainMember,
                        Applicant
                    ).join(Applicant, (MainMember.applicant_id==Applicant.id)).filter(
                        MainMember.state == MainMember.STATE_ACTIVE,
                        Applicant.consultant_id == consultant.id,
                        Applicant.status != 'lapsed',
                        or_(
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.last_name.ilike('{}%'.format(search_field)),
                            MainMember.id_number.ilike('{}%'.format(search_field)),
                            Applicant.policy_num.ilike('{}%'.format(search_field)) 
                        )
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])

                    resp.body = json.dumps([main_member[0].to_dict() for main_member in main_members], default=str)
                else:
                    applicants = session.query(Applicant).filter(
                        Applicant.state == Applicant.STATE_ACTIVE,
                        Applicant.status != 'lapsed',
                        Applicant.consultant_id == consultant.id
                    ).order_by(Applicant.id.desc())

                    if status:
                        applicants = applicants.filter(Applicant.status == status.lower()).all()

                    applicant_res = [(applicant, applicant.plan) for applicant in applicants]
                    if applicant_res:
                        for applicant in applicant_res:
                            if applicant[0].plan.id == applicant[1].id:
                                max_age_limit = applicant[1].member_maximum_age
                                min_age_limit = applicant[1].member_minimum_age
                                main_member = session.query(MainMember).filter(
                                    MainMember.state == MainMember.STATE_ACTIVE,
                                    MainMember.applicant_id == applicant[0].id
                                ).first()
                                if main_member:
                                    id_number = main_member.id_number

                                    number = int(id_number[0:2])
                                    if number == 0:
                                        number = 2000

                                    dob = datetime.datetime(number, int(id_number[2:4]), int(id_number[4:6]),0,0,0,0)
                                    now = datetime.datetime.now()
                                    age = relativedelta(now, dob)

                                    years = "{}".format(age.years)

                                    if len(years) > 2:
                                        years = years[2:]

                                    if int(years) > max_age_limit:
                                        main_member.age_limit_exceeded = True
                                    elif int(years) < min_age_limit:
                                        main_member.age_limit_exceeded = True
                                        session.commit()
                    applicant_ids = [applicant.id for applicant in applicants]
                    if notice:
                        main_members = session.query(MainMember).filter(
                            MainMember.state == MainMember.STATE_ACTIVE,
                            MainMember.age_limit_exceeded == True,
                            MainMember.applicant_id.in_(applicant_ids)
                        ).all()
                    else:
                        main_members = session.query(MainMember).filter(
                            MainMember.state == MainMember.STATE_ACTIVE,
                            MainMember.applicant_id.in_(applicant_ids)
                        ).all()

                    if not main_members:
                        resp.body = json.dumps([])
                    else:
                        resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class MainGetAllArchivedParlourEndpoint:
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
                try:
                    status = None
                    search_field = None
                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "search_string" in req.params:
                        search_field = req.params.pop("search_string")

                    parlour = session.query(Parlour).filter(
                        Parlour.state == Parlour.STATE_ACTIVE,
                        Parlour.id == id
                    ).one()
                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")
                except NoResultFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if search_field:
                    main_members = session.query(
                        MainMember,
                        Applicant
                    ).join(Applicant, (MainMember.applicant_id==Applicant.id)).filter(
                        MainMember.state == MainMember.STATE_ACTIVE,
                        Applicant.parlour_id == parlour.id,
                        Applicant.status == 'lapsed',
                        or_(
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.last_name.ilike('{}%'.format(search_field)),
                            MainMember.id_number.ilike('{}%'.format(search_field)),
                            Applicant.policy_num.ilike('{}%'.format(search_field))
                        )
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])

                    resp.body = json.dumps([main_member[0].to_dict() for main_member in main_members], default=str)
                else:
                    applicants = session.query(Applicant).filter(
                        or_(Applicant.state != Applicant.STATE_ACTIVE,
                            Applicant.status == 'lapsed'),
                            Applicant.parlour_id == parlour.id
                    ).order_by(Applicant.id.desc())

                    if status:
                        applicants = applicants.filter(Applicant.status == status.lower()).all()

                    applicant_ids = [applicant.id for applicant in applicants]
                    main_members = session.query(MainMember).filter(
                        or_(MainMember.state != MainMember.STATE_ACTIVE,
                            MainMember.applicant_id.in_(applicant_ids)),
                            MainMember.parlour_id == parlour.id
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])
                    else:
                        resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class MainGetAllArchivedConsultantEndpoint:
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
                try:
                    status = None
                    search_field = None

                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "search_string" in req.params:
                        search_field = req.params.pop("search_string")

                    consultant = session.query(Consultant).filter(
                        Consultant.state == Consultant.STATE_ACTIVE,
                        Consultant.id == id
                    ).one_or_none()
                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if search_field:
                    main_members = session.query(
                        MainMember,
                        Applicant
                    ).join(Applicant, (MainMember.applicant_id==Applicant.id)).filter(
                        or_(MainMember.state != MainMember.STATE_ARCHIVED,
                            Applicant.status == 'lapsed'),
                        or_(
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.id_number.ilike('{}%'.format(search_field)),
                            Applicant.policy_num.ilike('{}%'.format(search_field)),
                            Applicant.consultant_id == consultant.id
                        )
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])

                    resp.body = json.dumps([main_member[0].to_dict() for main_member in main_members], default=str)
                else:
                    applicants = session.query(Applicant).filter(
                        or_(Applicant.state != Applicant.STATE_ACTIVE,
                            Applicant.status == 'lapsed'),
                            Applicant.consultant_id == consultant.id
                    ).order_by(Applicant.id.desc())

                    if status:
                        applicants = applicants.filter(Applicant.status == status.lower()).all()

                    applicant_ids = [applicant.id for applicant in applicants]
                    main_members = session.query(MainMember).filter(
                        MainMember.state != MainMember.STATE_ACTIVE,
                        MainMember.applicant_id.in_(applicant_ids)
                    ).all()

                    if not main_members:
                        resp.body = json.dumps([])
                    else:
                        resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class MemberCertificateGetEndpoint:
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
                # req = json.loads(req.stream.read().decode('utf-8'))

                main_meber = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.state == MainMember.STATE_ACTIVE
                ).first()
                if main_meber is None:
                    raise falcon.HTTPNotFound(title="Error", description="Main member not found")

                applicant = session.query(Applicant).filter(
                    Applicant.id == main_meber.applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE
                ).first()

                if applicant is None:
                    raise falcon.HTTPNotFound(title="Error", description="Applicant not found")

                with open(applicant.document, 'rb') as f:
                    resp.downloadable_as = applicant.document
                    resp.content_type = 'application/pdf'
                    resp.stream = [f.read()]
                    resp.status = falcon.HTTP_200

        except:
            logger.exception("Error, Failed to get Payment with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Invoice with ID {}.".format(id))


class MemberPersonalDocsGetEndpoint:
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

                main_meber = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.state == MainMember.STATE_ACTIVE
                ).first()
                if main_meber is None:
                    raise falcon.HTTPNotFound(title="Error", description="Main member not found")

                applicant = session.query(Applicant).filter(
                    Applicant.id == main_meber.applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE
                ).first()

                if applicant is None:
                    raise falcon.HTTPNotFound(title="Error", description="Applicant not found")

                with open(applicant.personal_docs, 'rb') as f:
                    resp.downloadable_as = applicant.personal_docs
                    resp.content_type = 'application/pdf'
                    resp.stream = [f.read()]
                    resp.status = falcon.HTTP_200

        except:
            logger.exception("Error, Failed to get Payment with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Invoice with ID {}.".format(id))


class MainMemberPostFileEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):

        with db.transaction() as session:
            try:

                try:
                    main_member = session.query(MainMember).filter(
                        MainMember.id == id,
                        MainMember.state == MainMember.STATE_ACTIVE
                    ).one_or_none()

                except NoResultFound:
                    raise falcon.HTTPBadRequest(title="Error", description="No results found.")
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Multiple results found.")

                applicant = session.query(Applicant).filter(
                    Applicant.id == main_member.applicant_id,
                    Applicant.state == Applicant.STATE_ACTIVE).first()

                if not applicant:
                    raise falcon.HTTPBadRequest(title="Error", description="No results found.")

                pdf = req.get_param("myFile")
  
                filename = "{uuid}.{ext}".format(uuid=uuid.uuid4(), ext='pdf')

                os.chdir('./assets/uploads/certificates')
                pdf_path = os.path.join(os.getcwd(), filename)
                with open(pdf_path, "wb") as pdf_file:
                    while True:
                        chunk = pdf.file.read()
                        pdf_file.write(chunk)
                        if not chunk:
                            break

                applicant.personal_docs = '{}/{}'.format(os.getcwd(), filename)
                os.chdir('../../..')
                resp.status = falcon.HTTP_200
                resp.location = filename

                resp.body = json.dumps("{name:" + pdf_path + "}")

            except Exception as e:
                logger.exception(
                    "Error, experienced error while creating Applicant.")
                raise e


class MainMemberPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):
        
        req = json.load(req.bounded_stream)

        with db.transaction() as session:
            parlour = session.query(Parlour).filter(
                Parlour.id == req["parlour_id"],
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest("Parlour does not exist.")
            if not req.get("id_number"):
                raise falcon.HTTPBadRequest(title="Error", description="Missing id_number field.")
            if not req.get("first_name"):
                raise falcon.HTTPBadRequest(title="Error", description="Missing first name field.")
            if not req.get("last_name"):
                raise falcon.HTTPBadRequest(title="Error", description="Missing last name field.")

            consultant = session.query(Consultant).get(id)

            if not consultant:
                raise falcon.HTTPBadRequest(title="Error", description="Consultant does not exist.")

            plan_id = req.get("plan_id")

            plan = session.query(Plan).filter(
                Plan.id == plan_id,
                Plan.state == Plan.STATE_ACTIVE).one_or_none()

            if not plan:
                raise falcon.HTTPBadRequest(title="Error", description="Plan does not exist.")

            applicant_req = req.get("applicant")

            if not applicant_req.get("policy_num"):
                raise falcon.HTTPBadRequest(title="Error", description="Missing policy number field.")

            id_number = session.query(MainMember).filter(MainMember.id_number == req.get("id_number"), MainMember.parlour_id == parlour.id).first()

            if id_number:
                raise falcon.HTTPBadRequest(title="Error", description="ID number already exists.")

            try:
                applicant = Applicant(
                    policy_num = applicant_req.get("policy_num"),
                    # personal_docs = applicant_req.get("file_path"),
                    # document = applicant_req.get("document"),
                    status = 'unpaid',
                    plan_id = plan.id,
                    consultant_id = consultant.id,
                    parlour_id = parlour.id,
                    old_url = False,
                    date = datetime.datetime.now(),
                    state = Applicant.STATE_ACTIVE,
                    modified_at = datetime.datetime.now(),
                    created_at = datetime.datetime.now()
                )

                applicant.save(session)

                main_member = MainMember(
                    first_name = req.get("first_name"),
                    last_name = req.get("last_name"),
                    id_number = req.get("id_number"),
                    contact = req.get("contact"),
                    date_of_birth = req.get("date_of_birth"),
                    parlour_id = parlour.id,
                    date_joined = datetime.datetime.now(),
                    state=MainMember.STATE_ACTIVE,
                    applicant_id = applicant.id,
                    modified_at = datetime.datetime.now(),
                    created_at = datetime.datetime.now()
                )

                min_age_limit = plan.member_minimum_age
                max_age_limit = plan.member_maximum_age

                id_number = main_member.id_number
                if int(id_number[0:2]) > 21:
                    number = '19{}'.format(id_number[0:2])
                else:
                    number = '20{}'.format(id_number[0:2])
                dob = '{}-{}-{}'.format(number, id_number[2:4], id_number[4:6])
                # dob = main_member.date_of_birth
                dob = datetime.datetime.strptime(dob, "%Y-%m-%d")
                now = datetime.datetime.now()

                age = relativedelta(now, dob)

                years = "{}".format(age.years)
                try:
                    if len(years) > 2 and int(years[2:4]) > max_age_limit:
                        main_member.age_limit_exceeded = True
                    elif int(years) > max_age_limit:
                        main_member.age_limit_exceeded = True
                except:
                    pass

                try:
                    if len(years) > 2 and int(years[2:4]) < min_age_limit:
                        main_member.age_limit_exceeded = True
                    elif int(years) < min_age_limit:
                        main_member.age_limit_exceeded = True
                except:
                    pass
                main_member.save(session)

                applicant = update_certificate(applicant)

                resp.body = json.dumps(main_member.to_dict(), default=str)
            except Exception as e:
                logger.exception(
                    "Error, experienced error while creating Applicant.")
                raise e


class MainMemberPutEndpoint:

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

                try:
                    parlour_id = req.get("parlour_id")

                    parlour = session.query(Parlour).filter(
                        Parlour.id == parlour_id).one()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Bad Request")
                except NoResultFound:
                    raise falcon.HTTPNotFound(title="Not Found", description="Parlour not found")

                if not req.get("id_number"):
                    raise falcon.HTTPBadRequest(title="Error", description="Missing id_number field.")
                if not req.get("first_name"):
                    raise falcon.HTTPBadRequest(title="Error", description="Missing first name field.")
                if not req.get("last_name"):
                    raise falcon.HTTPBadRequest(title="Error", description="Missing last name field.")

                applicant_req = req.get("applicant")

                plan_id = req.get("plan_id")

                plan = session.query(Plan).filter(
                    Plan.id == plan_id,
                    Plan.state == Plan.STATE_ACTIVE).one_or_none()

                applicant = session.query(Applicant).filter(
                    Applicant.id == applicant_req.get("id"),
                    Applicant.parlour_id == parlour.id,
                    Applicant.state == Applicant.STATE_ACTIVE).first()

                if not applicant:
                    raise falcon.HTTPNotFound(title="Applicant not found", description="Could not find Applicant with given ID.")

                if plan:
                    applicant.plan_id = plan.id
                applicant.policy_num = applicant_req.get("policy_num")
                applicant.address = applicant_req.get("address")
                if applicant_req.get("document"):
                    applicant.document = applicant_req.get("document")
                    applicant.old_url = False

                main_member = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.parlour_id == parlour.id,
                    MainMember.state == MainMember.STATE_ACTIVE).first()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Main member not found", description="Could not find Applicant with given ID.")

                id_number_exists = session.query(MainMember).filter(MainMember.id_number == req.get("id_number"), MainMember.parlour_id == parlour.id).first()

                if id_number_exists and main_member.id_number != id_number_exists.id_number:
                    raise falcon.HTTPBadRequest(title="Error", description="ID number already exists.")

                main_member.first_name = req.get("first_name")
                main_member.last_name = req.get("last_name")
                main_member.id_number = req.get("id_number")
                main_member.contact = req.get("contact")
                main_member.date_of_birth = req.get("date_of_birth")
                main_member.parlour_id = parlour.id
                main_member.applicant_id = applicant.id

                applicant = update_certificate(applicant)

                main_member.save(session)
                resp.body = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class MainMemberPutAgeLimitExceptionEndpoint:

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

                main_member = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.state == MainMember.STATE_ACTIVE).first()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Main member not found", description="Could not find Applicant with given ID.")

                main_member.age_limit_exception = req.get("age_limit_exception")

                main_member.save(session)

                resp.body = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class MainMemberRestorePutEndpoint:

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
                try:
                    parlour = session.query(Parlour).filter(
                        Parlour.id == req.get("parlour")['id']).one()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Bad Request")
                except NoResultFound:
                    raise falcon.HTTPNotFound(title="Not Found", description="Parlour not found")

                main_member = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.parlour_id == parlour.id).first()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Main member not found", description="Could not find Applicant with given ID.")

                main_member.state = MainMember.STATE_ACTIVE
                applicant = session.query(Applicant).get(main_member.applicant_id)
                applicant.state = Applicant.STATE_ACTIVE

                main_member.save(session)

                resp.body = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class MainMemberDeleteEndpoint:

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
                try:
                    main_member = session.query(MainMember).get(id)
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Bad Request")
                except NoResultFound:
                    raise falcon.HTTPNotFound(title="Not Found", description="Member not found")

                if main_member.is_deleted:
                    falcon.HTTPNotFound(title="Not Found", description="Member does not exist.")

                main_member.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Bad Request", description="Failed to delete Applicant with ID {}.".format(id))


class MainMemberDownloadCSVGetEndpoint:

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
                parlour = session.query(Parlour).filter(
                    Parlour.id == id,
                    Parlour.state == Parlour.STATE_ACTIVE).first()

                if not parlour:
                    raise falcon.HTTPBadRequest("Parlour does not exist.")

                main_members = session.query(MainMember).join(
                    Applicant, (MainMember.applicant_id==Applicant.id)
                ).join(Plan, (Applicant.plan_id==Plan.id)).filter(MainMember.parlour_id==parlour.id).all()

                if not main_members:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


    def csv_dump(self, session, parlour_id):

        folder = os.path.dirname(__file__)

        today = datetime.datetime.today()

        logger.info('Create CSV file...')
        filename = os.path.join(folder, 'applicants_{}.xlsx'.format(today))

        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow([
                'First Name',
                'Last Name',
                'ID Number',
                'Contact Number',
                'Policy Number',
                'Date',
                'Status',
                'Cover',
                'Premium'
            ])

            main_members = session.query(MainMember).join(
                Applicant, (MainMember.applicant_id==Applicant.id)
            ).join(Plan, (Applicant.plan_id==Plan.id)).filter(MainMember.parlour_id==parlour_id).all()

            for main_member in main_members:
                member_dict = main_member.to_dict()
                writer.writerow([
                    member_dict.get("first_name"),
                    member_dict.get("last_name"),
                    member_dict.get("id_number"),
                    member_dict.get("contact"),
                    member_dict.get("applicant").get("policy_num"),
                    member_dict.get("date_joined"),
                    member_dict.get("applicant").get("status"),
                    member_dict.get("applicant").get("cover"),
                    member_dict.get("applicant").get("premium")
                ])


class ApplicantExportToExcelEndpoint:
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
                try:
                    status = None
                    permission = None
                    parlour = None
                    consultant = None

                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "permission" in req.params:
                        permission = req.params.pop("permission")

                    if permission.lower() == 'consultant':
                        consultant = session.query(Consultant).filter(
                            Consultant.state == Consultant.STATE_ACTIVE,
                            Consultant.id == id
                        ).one_or_none()

                    if permission.lower() == 'parlour':
                        parlour = session.query(Parlour).filter(
                            Parlour.state == Parlour.STATE_ACTIVE,
                            Parlour.id == id
                        ).one_or_none()
                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if consultant:
                    applicants = session.query(Applicant).filter(
                        Applicant.state == Applicant.STATE_ACTIVE,
                        Applicant.status != 'lapsed',
                        Applicant.consultant_id == consultant.id
                    ).order_by(Applicant.id.desc())

                if parlour:
                    applicants = session.query(Applicant).filter(
                        Applicant.state == Applicant.STATE_ACTIVE,
                        Applicant.status != 'lapsed',
                        Applicant.parlour_id == parlour.id
                    ).order_by(Applicant.id.desc())

                if status:
                    applicants = applicants.filter(Applicant.status == status.lower()).all()

                applicant_ids = [applicant.id for applicant in applicants]

                if not applicant_ids:
                    raise falcon.HTTPBadRequest(title="Error", description="No Applicants available")

                main_members = session.query(MainMember).filter(
                    MainMember.state == MainMember.STATE_ACTIVE,
                    MainMember.applicant_id.in_(applicant_ids)
                ).all()
                results = []

                for main in main_members:
                    d = main.to_short_dict()
                    results.append(d)

                    extended_members = session.query(ExtendedMember).filter(
                        ExtendedMember.state == ExtendedMember.STATE_ACTIVE,
                        ExtendedMember.applicant_id == main.applicant.id
                    ).all()
                    for ex in extended_members:
                       e = ex.to_short_dict()
                       results.append(e)

                if results:
                    data = []
                    for res in results:
                        applicant = res.get('applicant')
                        plan = applicant.get('plan')

                        data.append({
                            'First Name': res.get('first_name'),
                            'Last Name': res.get('last_name'),
                            'ID Number': res.get('id_number') if res.get('id_number') else res.get('date_of_birth'),
                            'Contact Number': res.get('contact') if res.get('contact') else res.get('number'),
                            'Date Joined': res.get('date_joined') if res.get('date_joined') else None,
                            'Status': applicant.get('status') if res.get else None,
                            'Premium': None if res.get('relation_to_main_member') else plan.get('premium'),
                            'Underwriter': None if res.get('relation_to_main_member') else plan.get('underwriter_premium'),
                            'Relation to Main Member': res.get('relation_to_main_member') if res.get('relation_to_main_member') else None,
                            })

                    df = pd.DataFrame(data)
                    filename = '{}_{}'.format(consultant.first_name, consultant.last_name) if consultant else parlour.parlourname
                    writer = pd.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter')
                    df.to_excel(writer, sheet_name='Sheet1', index=False)
                    os.chdir('./assets/uploads/spreadsheets')
                    path = os.getcwd()
                    writer.save()
                    os.chdir('../../..')

                    with open('{}/{}.xlsx'.format(path, filename), 'rb') as f:
                        resp.downloadable_as = '{}.xls'.format(filename)
                        resp.content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        resp.stream = [f.read()]
                        resp.status = falcon.HTTP_200

        except Exception as e:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise e


class SMSService:
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        import requests
        rest_dict = json.load(req.bounded_stream)
        with db.transaction() as session:
            status = None
            search_field = None
            contacts = None

            message = rest_dict.get("message")
            if not message:
                raise falcon.HTTPBadRequest(title="Missing Field", description="Message cannot be empty when sending an sms.")

            if rest_dict["to"]:
                cons = rest_dict.get("to").split(',')
                contacts = [''.join(['+27', contact[1:].strip()]) if len(contact) == 10 else contact.strip() for contact in cons]

            if rest_dict['state']:
                status = rest_dict.get("state")

            if rest_dict["search_string"]:
                search_field = rest_dict.get("search_string")

            parlour = session.query(Parlour).filter(
                Parlour.id == rest_dict["parlour_id"],
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

            if search_field:
                    main_members = session.query(
                        MainMember,
                        Applicant
                    ).join(Applicant, (MainMember.applicant_id==Applicant.id)).filter(
                        MainMember.state == MainMember.STATE_ACTIVE,
                        Applicant.parlour_id == parlour.id,
                        Applicant.status != 'lapsed',
                        or_(
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.first_name.ilike('{}%'.format(search_field)),
                            MainMember.id_number.ilike('{}%'.format(search_field)),
                            Applicant.policy_num.ilike('{}%'.format(search_field))
                        )
                    )

            if status:
                applicants = session.query(Applicant).filter(
                    Applicant.status == status,
                    Applicant.parlour_id== parlour.id
                ).all()
                applicant_ids = [applicant.id for applicant in applicants]
                main_members = session.query(MainMember).filter(
                    MainMember.state == MainMember.STATE_ACTIVE,
                    MainMember.applicant_id.in_(applicant_ids)
                )
            if not status and not search_field:
                main_members = session.query(MainMember).filter(
                    MainMember.state == MainMember.STATE_ACTIVE,
                    MainMember.parlour_id == parlour.id
                )

            if rest_dict['start_date']:
                start_date = rest_dict['start_date']
                main_members = main_members.filter(
                    MainMember.created_at >= start_date
                )

            if rest_dict['end_date']:
                end_date = rest_dict['end_date']
                main_members = main_members.filter(
                    MainMember.created_at <= end_date
                )

            if not contacts:
                contacts = [m.localize_contact() for m in main_members.all()]
            else:
                contacts = [''.join(['+27', contact[1:]]) if len(contact) == 10 else contact for contact in contacts]

            if parlour.number_of_sms < len(contacts):
                raise falcon.HTTPBadRequest(title="Error", description="You need more smses to use this service.")

            headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": conf.SMS_AUTH_TOKEN}
            response = requests.post('https://api.bulksms.com/v1/messages', headers=headers, json={'from': conf.SMS_FROM_NUMBER, 'to': contacts,  'body': '{}: {}'.format(parlour.parlourname.title(), message)})
            parlour.number_of_sms = parlour.number_of_sms - len(contacts) if parlour.number_of_sms > len(contacts) else 0

            result = {'status_code': response.status_code, 'parlour': parlour.to_dict()}
            resp.body = json.dumps(result, default=str)
