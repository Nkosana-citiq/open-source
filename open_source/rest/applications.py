import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant

logger = logging.getLogger(__name__)


class ApplicantGetEndpoint:

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                applicant = session.query(Applicant).filter(
                    Applicant.id == id,
                    Applicant.state == Applicant.STATE_ACTIVE
                ).first()
                if applicant is None:
                    raise falcon.HTTPNotFound(title="Applicant Not Found")

                resp.text = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Applicant with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicant with ID {}.".format(id))


class ApplicantGetAllEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                applicants = session.query(Applicant).filter(Applicant.state == Applicant.STATE_ACTIVE).all()
                if applicants:
                    resp.text = json.dumps([applicant.to_dict() for applicant in applicants], default=str)
                resp.body = json.dumps([])
                
        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Applicants for user with ID {}.".format(id))


class ApplicantPostEndpoint:

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                applicant = Applicant(
                    policy_num = req["policy_num"],
                    document = req["document"],
                    date = req["date"],
                    state = req["state"],
                    status = req["status"],
                    canceled = req["canceled"],
                    modified = req["modified_at"],
                    created = req["created_at"],
                    parlour = req["parlour"],
                    consultant = req["consultant"],
                    state=Applicant.STATE_ACTIVE,
                )
                applicant.save(session)
                resp.text = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Applicant.")


class ApplicantPutEndpoint:

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:

                applicant = session.query(Applicant).filter(
                    Applicant.id == id).first()

                if not applicant:
                    raise falcon.HTTPNotFound(title="Applicant not found", description="Could not find Applicant with given ID.")

                applicant.policy_num = req["policy_num"]
                applicant.document = req["document"]
                applicant.date = req["date"]
                applicant.state = req["state"]
                applicant.status = req["status"]
                applicant.canceled = req["canceled"]
                applicant.modified = req["modified_at"]
                applicant.created = req["created_at"]
                applicant.parlour = req["parlour"]
                applicant.consultant = req["consultant"]
                applicant.state=Applicant.STATE_ACTIVE
                
                applicant.save(session)
                resp.text = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Applicant.")


class ApplicantDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                applicant = session.query(Applicant).filter(Applicant.id == id).first()

                if applicant is None:
                    raise falcon.HTTPNotFound(title="Applicant Not Found")
                if applicant.is_deleted:
                    falcon.HTTPNotFound("Applicant does not exist.")

                applicant.delete(session)
                resp.text = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Applicant with ID {}.".format(id))
