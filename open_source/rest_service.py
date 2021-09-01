import logging

import falcon
from falcon_cors import CORS
from open_source import config

logging.basicConfig(level=logging.INFO)

from open_source.rest import middleware
from open_source.rest import applicants, consultants, main_members, parlours, plans

allowed_origins = None

if config.get_config().is_prod():
    allowed_origins = []
elif config.get_config().is_preprod():
    allowed_origins = []

if allowed_origins:
    cors = CORS(
        allow_origins_list=allowed_origins,
        allow_all_methods=True,
        allow_all_headers=True)

else:
    cors = CORS(
        allow_all_origins=True,
        allow_all_methods=True,
        allow_all_headers=True)

# cors = CORS(allow_all_origins=True, allow_all_methods=True, allow_all_headers=True)

api = falcon.API(
    middleware=[cors.middleware,
    middleware.AuthMiddleware()]
    # middleware.PermissionMiddleware()
)

api.add_route('/open-source/parlours/', parlours.ParlourGetAllEndpoint())
api.add_route('/open-source/parlours/pending', parlours.ParlourGetAllPendingEndpoint())
api.add_route('/open-source/parlours/archived', parlours.ParlourGetAllArchivedEndpoint())
api.add_route('/open-source/parlours', parlours.ParlourPostEndpoint())
api.add_route('/open-source/parlours/{id}', parlours.ParlourGetEndpoint())
api.add_route('/open-source/parlours/{id}/update', parlours.ParlourPutEndpoint())
api.add_route('/open-source/parlours/{id}/delete', parlours.ParlourDeleteEndpoint())
api.add_route('/open-source/parlours/signin', parlours.ParlourAuthEndpoint())
api.add_route('/open-source/parlours/signup', parlours.ParlourSignupEndpoint())


api.add_route('/open-source/plans/parlour/{id}', plans.PlanGetAllEndpoint())
api.add_route('/open-source/plans', plans.PlanPostEndpoint())
api.add_route('/open-source/plans/{id}', plans.PlanGetEndpoint())
api.add_route('/open-source/plans/{id}/update', plans.PlanPutEndpoint())
api.add_route('/open-source/plans/{id}/delete', plans.PlanDeleteEndpoint())

api.add_route('/open-source/consultants/parlour/{id}', consultants.ConsultantGetAllEndpoint())
api.add_route('/open-source/consultants/pending', consultants.ConsultantGetAllPendingEndpoint())
api.add_route('/open-source/consultants/archived', consultants.ConsultantGetAllArchivedEndpoint())
api.add_route('/open-source/consultants', consultants.ConsultantPostEndpoint())
api.add_route('/open-source/consultants/{id}', consultants.ConsultantGetEndpoint())
api.add_route('/open-source/consultants/{id}/update', consultants.ConsultantPutEndpoint())
api.add_route('/open-source/consultants/{id}/delete', consultants.ConsultantDeleteEndpoint())
api.add_route('/open-source/consultants/signin', consultants.ConsultantAuthEndpoint())
api.add_route('/open-source/consultants/signup', consultants.ConsultantSignupEndpoint())
api.add_route('/open-source/consultants/{id}/actions/change_password', consultants.ChangeUserPasswordEndpoint())

api.add_route('/open-source/applicants/consultant/{id}', applicants.ApplicantGetAllEndpoint())
api.add_route('/open-source/applicants', applicants.ApplicantPostEndpoint())
api.add_route('/open-source/applicants/{id}', applicants.ApplicantGetEndpoint())
api.add_route('/open-source/applicants/{id}/update', applicants.ApplicantPutEndpoint())
api.add_route('/open-source/applicants/{id}/delete', applicants.ApplicantDeleteEndpoint())

api.add_route('/open-source/main-members/consultant/{id}', main_members.MainMemberGetAllEndpoint())
api.add_route('/open-source/main-members', main_members.MainMemberPostEndpoint())
api.add_route('/open-source/main-members/{id}', main_members.MainMemberGetEndpoint())
api.add_route('/open-source/main-members/{id}/update', main_members.MainMemberPutEndpoint())
api.add_route('/open-source/main-members/{id}/delete', main_members.MainMemberDeleteEndpoint())

# api.add_route('/open-source/extended-members/consultant/{id}', main_members.MainMemberGetAllEndpoint())
# api.add_route('/open-source/extended-members', main_members.MainMemberPostEndpoint())
# api.add_route('/open-source/extended-members/{id}', main_members.MainMemberGetEndpoint())
# api.add_route('/open-source/extended-members/{id}/update', main_members.MainMemberPutEndpoint())
# api.add_route('/open-source/extended-members/{id}/delete', main_members.MainMemberDeleteEndpoint())


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8009, api)
    httpd.serve_forever()
