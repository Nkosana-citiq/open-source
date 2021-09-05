from datetime import datetime
from open_source.core import extended_members
from open_source.core import applicants
from open_source.core.extended_members import ExtendedMember
from open_source.core.applicants import Applicant
from falcon_cors import CORS

import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant

logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

class ExtendedMemberGetEndpoint:

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
                applicant = session.query(Applicant).filter(
                    Applicant.state == Applicant.STATE_ACTIVE,
                    Applicant.id == id
                ).one_or_none()
                print("Applicant: ", applicant.to_dict())
                if not applicant:
                    raise falcon.HTTPBadRequest()

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


class ExtendedMembersPostEndpoint:

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

                extended_member = ExtendedMember(
                    first_name = req["first_name"],
                    last_name = req["last_name"],
                    number = req["number"],
                    date_of_birth = req["date_of_birth"],
                    applicant_id = applicant.id,
                    date_joined = req['date_joined'],
                    state=ExtendedMember.STATE_ACTIVE,
                    created_at = datetime.now(),
                    modified_at = datetime.now()
                )

                extended_member.save(session)
                resp.body = json.dumps(extended_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Applicant.")
            raise falcon.HTTPBadRequest(title="Bad Request",
                description="Processing Failed. experienced error while creating Applicant.")


# class ApplicantPutEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_put(self, req, resp, id):
#         req = json.loads(req.stream.read().decode('utf-8'))
#         try:
#             with db.transaction() as session:

#                 applicant = session.query(Applicant).filter(
#                     Applicant.id == id).first()

#                 consultant = session.query(Consultant).filter(
#                     Consultant.id == req["consultant_id"],
#                     Consultant.state == Consultant.STATE_ACTIVE).first()

#                 if not applicant:
#                     raise falcon.HTTPNotFound(title="Applicant not found", description="Could not find Applicant with given ID.")

#                 applicant.policy_num = req["policy_num"]
#                 applicant.document = req["document"]
#                 applicant.date = req["date"]
#                 # applicant.state = req["state"]
#                 applicant.status = req["status"]
#                 applicant.canceled = req["canceled"]
#                 applicant.parlour_id = req["parlour_id"]
#                 applicant.consultant_id = req["consultant_id"]
#                 applicant.state=Applicant.STATE_ACTIVE

#                 # AuditLogClient.save_log(
#                 #     session,
#                 #     consultant.consultant_id,
#                 #     consultant.email,
#                 #     data_new=applicant.to_dict(),
#                 #     notes='New applicant with ID [{}] added by consultant {} {}'.format(
#                 #         applicant.id, consultant.first_name, consultant.last_name)
#                 # )
#                 applicant.save(session)
#                 resp.body = json.dumps(applicant.to_dict(), default=str)
#         except:
#             logger.exception(
#                 "Error, experienced error while creating Applicant.")
#             raise falcon.HTTP_BAD_REQUEST(
#                 "Processing Failed. experienced error while creating Applicant.")


# class ApplicantDeleteEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_delete(self, req, resp, id):
#         try:
#             with db.transaction() as session:
#                 applicant = session.query(Applicant).filter(Applicant.id == id).first()

#                 if applicant is None:
#                     raise falcon.HTTPNotFound(title="Applicant Not Found")
#                 if applicant.is_deleted:
#                     falcon.HTTPNotFound("Applicant does not exist.")

#                 applicant.delete(session)
#                 resp.body = json.dumps({})
#         except:
#             logger.exception("Error, Failed to delete Applicant with ID {}.".format(id))
#             raise falcon.HTTP_BAD_REQUEST("Failed to delete Applicant with ID {}.".format(id))
