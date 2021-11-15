import datetime
import falcon
import json
import logging

from open_source import db

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from open_source.core.applicants import Applicant
from open_source.core.dependants import Dependant
from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from falcon_cors import CORS




logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)


class DependantMembersGetAllEndpoint:
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
                applicant = session.query(Applicant).filter(
                    Applicant.state == Applicant.STATE_ACTIVE,
                    Applicant.id == id
                ).one_or_none()

                if not applicant:
                    raise falcon.HTTPBadRequest()

                additional_extended_members = session.query(Dependant).filter(
                    Dependant.state == Dependant.STATE_ACTIVE,
                    Dependant.applicant_id == applicant.id
                ).all()

                if not additional_extended_members:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([dependant.to_dict() for dependant in additional_extended_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Extended Members for user with ID {}.".format(id))



class DependantPostEndpoint:

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

                applicant = session.query(Applicant).filter(
                    Applicant.id == req["applicant_id"],
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")

                dependant = Dependant(
                    first_name = req["first_name"],
                    last_name = req["last_name"],
                    number = req["number"],
                    date_of_birth = req["date_of_birth"],
                    applicant_id = applicant.id,
                    date_joined = req['date_joined'],
                    state=Dependant.STATE_ACTIVE,
                    created_at = datetime.now(),
                    modified_at = datetime.now()
                )

                dependant.save(session)
                resp.body = json.dumps(dependant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(title="Bad Request",
                description="Processing Failed. experienced error while creating Applicant.")


class DependantPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))

        try:
            with db.transaction() as session:

                applicant = session.query(Applicant).filter(
                    Applicant.id == req["applicant_id"],
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")

                dependant = session.query(Dependant).filter(
                    Dependant.id == id,
                    Dependant.state == Dependant.STATE_ACTIVE).first()

                if not dependant:
                    raise falcon.HTTPNotFound(title="Dependant not found", description="Could not find Applicant with given ID.")

                dependant.first_name = req["first_name"],
                dependant.last_name = req["last_name"],
                dependant.number = req["number"],
                dependant.date_of_birth = req["date_of_birth"],
                dependant.applicant_id = applicant.id,
                dependant.date_joined = req['date_joined'],
                dependant.modified_at = datetime.now()

                dependant.save(session)
                resp.body = json.dumps(dependant.to_dict(), default=str)

        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(title="Bad Request",
                description="Processing Failed. experienced error while creating Applicant.")


class DependantDeleteEndpoint:

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
                dependant = session.query(Dependant).get(id)

                if dependant is None:
                    raise falcon.HTTPNotFound(title="Applicant Not Found")
                if dependant.is_deleted:
                    falcon.HTTPNotFound("Applicant does not exist.")

                dependant.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Applicant with ID {}.".format(id))

