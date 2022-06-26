# import datetime
# import falcon
# import json
# import logging

# from open_source import db
# from open_source.core import additional_extended_members

# from open_source.core.main_members import MainMember
# from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

# from open_source.core.additional_extended_members import AdditionalExtendedMember
# from open_source.core.parlours import Parlour
# from open_source.core.consultants import Consultant
# from falcon_cors import CORS


# logger = logging.getLogger(__name__)
# public_cors = CORS(allow_all_origins=True)

# class AdditionalExtendedMembersGetAllEndpoint:
#     cors = public_cors
#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_get(self, req, resp, id):
#         try:
#             with db.transaction() as session:
#                 applicant = session.query(MainMember).filter(
#                     MainMember.state == MainMember.STATE_ACTIVE,
#                     MainMember.id == id
#                 ).one_or_none()

#                 if not applicant:
#                     raise falcon.HTTPBadRequest()

#                 additional_extended_members = session.query(AdditionalExtendedMember).filter(
#                     AdditionalExtendedMember.state == AdditionalExtendedMember.STATE_ACTIVE,
#                     AdditionalExtendedMember.main_member_id == applicant.id
#                 ).all()

#                 if not additional_extended_members:
#                     resp.body = json.dumps([])
#                 else:
#                     resp.body = json.dumps([additional_extended_member.to_dict() for additional_extended_member in additional_extended_members], default=str)

#         except:
#             logger.exception("Error, Failed to get Main Members for user with ID {}.".format(id))
#             raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Extended Members for user with ID {}.".format(id))


# class AdditionalExtendedMembersPostEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_post(self, req, resp):
#         req = json.loads(req.stream.read().decode('utf-8'))

#         try:
#             with db.transaction() as session:

#                 applicant = session.query(MainMember).filter(
#                     MainMember.id == req["main_member_id"],
#                     MainMember.state == MainMember.STATE_ACTIVE).one_or_none()

#                 if not applicant:
#                     raise falcon.HTTPNotFound(title="404 Not Found", description="MainMember does not foumd.")

#                 additional_extended_member = AdditionalExtendedMember(
#                     first_name = req["first_name"],
#                     last_name = req["last_name"],
#                     number = req["number"],
#                     date_of_birth = req["date_of_birth"],
#                     main_member_id = applicant.id,
#                     date_joined = req['date_joined'],
#                     state=AdditionalExtendedMember.STATE_ACTIVE,
#                     created_at = datetime.now(),
#                     modified_at = datetime.now()
#                 )

#                 additional_extended_member.save(session)
#                 resp.body = json.dumps(additional_extended_member.to_dict(), default=str)
#         except:
#             logger.exception(
#                 "Error, experienced error while creating MainMember.")
#             raise falcon.HTTPBadRequest(title="Bad Request",
#                 description="Processing Failed. experienced error while creating MainMember.")


# class AdditionalExtendedMemberPutEndpoint:

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

#                 applicant = session.query(MainMember).filter(
#                     MainMember.id == req["main_member_id"],
#                     MainMember.state == MainMember.STATE_ACTIVE).one_or_none()

#                 if not applicant:
#                     raise falcon.HTTPNotFound(title="404 Not Found", description="MainMember does not foumd.")

#                 additional_extended_member = session.query(AdditionalExtendedMember).filter(
#                     AdditionalExtendedMember.id == id,
#                     AdditionalExtendedMember.main_member_id == applicant.id,
#                     AdditionalExtendedMember.state == AdditionalExtendedMember.STATE_ACTIVE).first()

#                 if not additional_extended_member:
#                     raise falcon.HTTPNotFound(title="Additiona Extened Member not found", description="Could not find MainMember with given ID.")

#                 additional_extended_member.first_name = req["first_name"],
#                 additional_extended_member.last_name = req["last_name"],
#                 additional_extended_member.number = req["number"],
#                 additional_extended_member.date_of_birth = req["date_of_birth"],
#                 additional_extended_member.main_member_id = applicant.id,
#                 additional_extended_member.date_joined = req['date_joined'],
#                 additional_extended_member.modified_at = datetime.now()

#                 additional_extended_member.save(session)
#                 resp.body = json.dumps(applicant.to_dict(), default=str)
#         except:
#             logger.exception(
#                 "Error, experienced error while creating MainMember.")
#             raise falcon.HTTPBadRequest(title="Error", 
#             description="Processing Failed. experienced error while creating MainMember.")


# class AdditionalExtendedMemberDeleteEndpoint:

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
#                 additional_extended_member = session.query(AdditionalExtendedMember).get(id)

#                 if additional_extended_member is None:
#                     raise falcon.HTTPNotFound(title="MainMember Not Found")
#                 if additional_extended_member.is_deleted:
#                     falcon.HTTPNotFound("MainMember does not exist.")

#                 additional_extended_member.delete(session)
#                 resp.body = json.dumps({})
#         except:
#             logger.exception("Error, Failed to delete MainMember with ID {}.".format(id))
#             raise falcon.HTTPBadRequest(title="Error", description="Failed to delete MainMember with ID {}.".format(id))
