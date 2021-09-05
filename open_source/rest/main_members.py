from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from open_source.core import applicants
from open_source.core import main_members
from open_source.core.main_members import MainMember
from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from falcon_cors import CORS

import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant

logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

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
                parlour = session.query(Parlour).filter(
                    Parlour.state == Parlour.STATE_ACTIVE,
                    Parlour.id == id
                ).one_or_none()

                if not parlour:
                    raise falcon.HTTPBadRequest()

                main_members = session.query(MainMember).filter(
                    MainMember.state == MainMember.STATE_ACTIVE,
                    MainMember.parlour_id == parlour.id
                ).all()

                if not main_members:
                    raise falcon.HTTPNotFound()

                resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class MainMemberPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))

        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(
                    Parlour.id == req["parlour_id"],
                    Parlour.state == Parlour.STATE_ACTIVE).first()

                if not parlour:
                    raise falcon.HTTPBadRequest("Parlour does not exist.")

                main_member = MainMember(
                    first_name = req["first_name"],
                    last_name = req["last_name"],
                    id_number = req["id_number"],
                    contact = req["contact"],
                    date_of_birth = req["date_of_birth"],
                    parlour_id = parlour.id,
                    applicant_id = req["applicant_id"],
                    date_joined = req['date_joined'],
                    state=MainMember.STATE_ACTIVE
                )

                main_member.save(session)
                resp.body = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class MainMemberPutEndpoint:
    cors = public_cors
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

                try:
                    parlour = session.query(Parlour).filter(
                        Parlour.id == req.get("parlour_id")).one()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Bad Request")
                except NoResultFound:
                    raise falcon.HTTPNotFound(title="Not Found", description="Parlour not found")

                main_member = session.query(MainMember).filter(
                    MainMember.id == id,
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Main member not found", description="Could not find Applicant with given ID.")

                main_member.first_name = req["first_name"],
                main_member.last_name = req["last_name"],
                main_member.id_number = req["id_number"],
                main_member.contact = req["contact"],
                main_member.date_of_birth = req["date_of_birth"],
                main_member.parlour_id = parlour.id,
                main_member.applicant_id = req["applicant_id"],
                main_member.date_joined = req['date_joined'],

                main_member.save(session)
                resp.body = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class MainMemberDeleteEndpoint:
    cors = public_cors
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
