from open_source.core import applicants
from open_source.core import consultants
from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from open_source.core.audit import AuditLogClient

import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant

logger = logging.getLogger(__name__)


class ApplicantGetEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        with db.transaction() as session:
            applicant = session.query(Applicant).filter(
                Applicant.id == id,
                Applicant.state == Applicant.STATE_ACTIVE
            ).first()
            if applicant is None:
                raise falcon.HTTPNotFound(title="Applicant Not Found")

            resp.body = json.dumps(applicant.to_dict(), default=str)


class ApplicantGetAllEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                applicants = session.query(Applicant).filter(
                    Applicant.state == Applicant.STATE_ACTIVE,
                    Applicant.consultant_id != 0
                ).all()

                if applicants:
                    resp.body = json.dumps([applicant.to_dict() for applicant in applicants], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class ApplicantPostEndpoint:

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

                consultant = session.query(Consultant).filter(
                    Consultant.id == req["consultant_id"],
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if not parlour:
                    raise falcon.HTTP_BAD_REQUEST("Parlour does not exist.")

                applicant = Applicant(
                    policy_num = req["policy_num"],
                    document = req["document"],
                    date = req["date"],
                    status = req["status"],
                    canceled = req["canceled"],
                    parlour_id = parlour.id,
                    consultant_id = req["consultant_id"],
                    plan_id = req['plan_id'],
                    state=Applicant.STATE_ACTIVE
                )

                applicant.save(session)
                resp.body = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Applicant.")


class ApplicantPutEndpoint:

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

                applicant = session.query(Applicant).filter(
                    Applicant.id == id).first()

                consultant = session.query(Consultant).filter(
                    Consultant.id == req["consultant_id"],
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if not applicant:
                    raise falcon.HTTPNotFound(title="Applicant not found", description="Could not find Applicant with given ID.")

                applicant.policy_num = req["policy_num"]
                applicant.document = req["document"]
                applicant.date = req["date"]
                # applicant.state = req["state"]
                applicant.status = req["status"]
                applicant.canceled = req["canceled"]
                applicant.parlour_id = req["parlour_id"]
                applicant.consultant_id = req["consultant_id"]
                applicant.state=Applicant.STATE_ACTIVE

                # AuditLogClient.save_log(
                #     session,
                #     consultant.consultant_id,
                #     consultant.email,
                #     data_new=applicant.to_dict(),
                #     notes='New applicant with ID [{}] added by consultant {} {}'.format(
                #         applicant.id, consultant.first_name, consultant.last_name)
                # )
                applicant.save(session)
                resp.body = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Applicant.")


class ApplicantDeleteEndpoint:

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
                applicant = session.query(Applicant).filter(Applicant.id == id).first()

                if applicant is None:
                    raise falcon.HTTPNotFound(title="Applicant Not Found")
                if applicant.is_deleted:
                    falcon.HTTPNotFound("Applicant does not exist.")

                applicant.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Applicant with ID {}.".format(id))
