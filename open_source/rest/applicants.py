# from open_source.core import main_members
# from open_source.core import consultants
# from open_source.core.parlours import Parlour
# from open_source.core.consultants import Consultant
# from open_source.core.audit import AuditLogClient

# import falcon
# import json
# import logging

# from open_source import db

# from open_source.core.main_members import MainMember

# logger = logging.getLogger(__name__)


# class ApplicantGetEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_get(self, req, resp, id):
#         with db.transaction() as session:
#             main_member = session.query(MainMember).filter(
#                 MainMember.id == id,
#                 MainMember.state == MainMember.STATE_ACTIVE
#             ).first()
#             if main_member is None:
#                 raise falcon.HTTPNotFound(title="MainMember Not Found")

#             resp.body = json.dumps(main_member.to_dict(), default=str)


# class ApplicantGetAllEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_get(self, req, resp):
#         try:
#             with db.transaction() as session:
#                 main_members = session.query(MainMember).filter(
#                     MainMember.state == MainMember.STATE_ACTIVE,
#                     MainMember.consultant_id != 0
#                 ).all()

#                 if main_members:
#                     resp.body = json.dumps([main_member.to_dict() for main_member in main_members], default=str)
#                 else:
#                     resp.body = json.dumps([])

#         except:
#             logger.exception("Error, Failed to get Main Members for user with ID {}.".format(id))
#             raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Main Members for user with ID {}.".format(id))


# class ApplicantPostEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_post(self, req, resp):
#         req = json.load(req.bounded_stream)

#         try:
#             with db.transaction() as session:
#                 parlour = session.query(Parlour).filter(
#                     Parlour.id == req["parlour_id"],
#                     Parlour.state == Parlour.STATE_ACTIVE).first()

#                 consultant = session.query(Consultant).filter(
#                     Consultant.id == req["consultant_id"],
#                     Consultant.state == Consultant.STATE_ACTIVE).first()

#                 if not parlour:
#                     raise falcon.HTTPBadRequest(title="Error", description="Parlour does not exist.")

#                 main_member = MainMember(
#                     policy_num = req["policy_num"],
#                     document = req["document"],
#                     date = req["date"],
#                     status = req["status"],
#                     canceled = req["canceled"],
#                     parlour_id = parlour.id,
#                     consultant_id = req["consultant_id"],
#                     plan_id = req['plan_id'],
#                     state=MainMember.STATE_ACTIVE
#                 )

#                 main_member.save(session)
#                 resp.body = json.dumps(main_member.to_dict(), default=str)
#         except:
#             logger.exception(
#                 "Error, experienced error while creating MainMember.")
#             raise falcon.HTTPBadRequest(
#                 "Processing Failed. experienced error while creating MainMember.")


# class ApplicantPutEndpoint:

#     def __init__(self, secure=False, basic_secure=False):
#         self.secure = secure
#         self.basic_secure = basic_secure

#     def is_basic_secure(self):
#         return self.basic_secure

#     def is_not_secure(self):
#         return not self.secure

#     def on_put(self, req, resp, id):
#         req = json.load(req.bounded_stream)
#         try:
#             with db.transaction() as session:

#                 main_member = session.query(MainMember).filter(
#                     MainMember.id == id).first()

#                 consultant = session.query(Consultant).filter(
#                     Consultant.id == req["consultant_id"],
#                     Consultant.state == Consultant.STATE_ACTIVE).first()

#                 if not main_member:
#                     raise falcon.HTTPNotFound(title="MainMember not found", description="Could not find MainMember with given ID.")

#                 main_member.policy_num = req["policy_num"]
#                 main_member.document = req["document"]
#                 main_member.date = req["date"]
#                 # main_member.state = req["state"]
#                 main_member.status = req["status"]
#                 main_member.canceled = req["canceled"]
#                 main_member.parlour_id = req["parlour_id"]
#                 main_member.consultant_id = req["consultant_id"]
#                 main_member.state=MainMember.STATE_ACTIVE

#                 main_member.save(session)
#                 resp.body = json.dumps(main_member.to_dict(), default=str)
#         except:
#             logger.exception(
#                 "Error, experienced error while creating MainMember.")
#             raise falcon.HTTPBadRequest(title="Error",
#             description="Processing Failed. experienced error while creating MainMember.")


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
#                 main_member = session.query(MainMember).filter(MainMember.id == id).first()

#                 if main_member is None:
#                     raise falcon.HTTPNotFound(title="MainMember Not Found")
#                 if main_member.is_deleted:
#                     falcon.HTTPNotFound("MainMember does not exist.")

#                 main_member.delete(session)
#                 resp.body = json.dumps({})
#         except:
#             logger.exception("Error, Failed to delete MainMember with ID {}.".format(id))
#             raise falcon.HTTPBadRequest(title="Error", description="Failed to delete MainMember with ID {}.".format(id))
