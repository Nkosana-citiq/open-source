import datetime
import falcon
import json
import logging

from open_source import db
from open_source.core import additional_extended_members

from open_source.core.applicants import Applicant
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from open_source.core.additional_extended_members import AdditionalExtendedMember
from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from falcon_cors import CORS


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

class AdditionalExtendedMembersGetAllEndpoint:
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

                additional_extended_members = session.query(AdditionalExtendedMember).filter(
                    AdditionalExtendedMember.state == AdditionalExtendedMember.STATE_ACTIVE,
                    AdditionalExtendedMember.applicant_id == applicant.id
                ).all()

                if not additional_extended_members:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([additional_extended_member.to_dict() for additional_extended_member in additional_extended_members], default=str)

        except:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Extended Members for user with ID {}.".format(id))


class AdditionalExtendedMembersPostEndpoint:

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

                additional_extended_member = AdditionalExtendedMember(
                    first_name = req["first_name"],
                    last_name = req["last_name"],
                    number = req["number"],
                    date_of_birth = req["date_of_birth"],
                    applicant_id = applicant.id,
                    date_joined = req['date_joined'],
                    state=AdditionalExtendedMember.STATE_ACTIVE,
                    created_at = datetime.now(),
                    modified_at = datetime.now()
                )

                additional_extended_member.save(session)
                resp.body = json.dumps(additional_extended_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(title="Bad Request",
                description="Processing Failed. experienced error while creating Applicant.")


class AdditionalExtendedMemberPutEndpoint:

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
                    Applicant.id == req["applicant_id"],
                    Applicant.state == Applicant.STATE_ACTIVE).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Applicant does not foumd.")

                additional_extended_member = session.query(AdditionalExtendedMember).filter(
                    AdditionalExtendedMember.id == id,
                    AdditionalExtendedMember.applicant_id == applicant.id,
                    AdditionalExtendedMember.state == AdditionalExtendedMember.STATE_ACTIVE).first()

                if not additional_extended_member:
                    raise falcon.HTTPNotFound(title="Additiona Extened Member not found", description="Could not find Applicant with given ID.")

                additional_extended_member.first_name = req["first_name"],
                additional_extended_member.last_name = req["last_name"],
                additional_extended_member.number = req["number"],
                additional_extended_member.date_of_birth = req["date_of_birth"],
                additional_extended_member.applicant_id = applicant.id,
                additional_extended_member.date_joined = req['date_joined'],
                additional_extended_member.modified_at = datetime.now()

                additional_extended_member.save(session)
                resp.body = json.dumps(applicant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(title="Error", 
            description="Processing Failed. experienced error while creating Applicant.")


class AdditionalExtendedMemberDeleteEndpoint:

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
                additional_extended_member = session.query(AdditionalExtendedMember).get(id)

                if additional_extended_member is None:
                    raise falcon.HTTPNotFound(title="Applicant Not Found")
                if additional_extended_member.is_deleted:
                    falcon.HTTPNotFound("Applicant does not exist.")

                additional_extended_member.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Applicant with ID {}.".format(id))
