import logging

import falcon
from falcon_cors import CORS
from open_source import config

logging.basicConfig(level=logging.INFO)

from open_source.rest import middleware
from open_source.rest import (
    applicants, consultants, parlours, plans,
    main_members, extended_members, payments,
    additional_extended_members, dependants, admins
)

from falcon_multipart.middleware import MultipartMiddleware


ALLOWED_ORIGINS = [
    "http://backend.osource.co.za",
    "https://backend.osource.co.za",
    "https://staging.osource.co.za",
    "https://nkosana-citiq.github.io",
    'http://localhost:8009',
    'http://127.0.0.1:8009',
    "http://osource.co.za",
    "https://osource.co.za"]

whitelisted_methods = [
    "GET",
    "PUT",
    "POST",
    "PATCH",
    "OPTIONS" # this is required for preflight request
]


cors = CORS(
    allow_all_origins=True,
    allow_all_methods=True,
    allow_all_headers=True)

api = application = falcon.API(
    middleware=[cors.middleware,
    MultipartMiddleware(),
    middleware.AuthMiddleware()]
)

api.add_route('/open-source/parlours/active', parlours.ParlourGetAllEndpoint())
api.add_route('/open-source/parlours/pending', parlours.ParlourGetAllPendingEndpoint())
api.add_route('/open-source/parlours/archived', parlours.ParlourGetAllArchivedEndpoint())
api.add_route('/open-source/parlours', parlours.ParlourPostEndpoint())
api.add_route('/open-source/parlours/{id}', parlours.ParlourGetEndpoint())
api.add_route('/open-source/parlours/{id}/update', parlours.ParlourPutEndpoint())
api.add_route('/open-source/parlours/{id}/suspend', parlours.ParlourSuspendEndpoint())
api.add_route('/open-source/parlours/{id}/activate', parlours.ParlourActivateEndpoint())
api.add_route('/open-source/parlours/{id}/action/sms', parlours.ParlourAddSMSEndpoint())
api.add_route('/open-source/parlours/{id}/delete', parlours.ParlourDeleteEndpoint())
api.add_route('/open-source/parlours/signin', parlours.ParlourAuthEndpoint())
api.add_route('/open-source/parlours/signup', parlours.ParlourSignupEndpoint())
api.add_route('/open-source/actions/reset_password', parlours.ResetPasswordPostEndpoint())


api.add_route('/open-source/parlours/{id}/plans/all', plans.PlanGetParlourAllEndpoint())
api.add_route('/open-source/plans', plans.PlanPostEndpoint())
api.add_route('/open-source/plans/{id}/get', plans.PlanGetEndpoint())
api.add_route('/open-source/plans/{id}/update', plans.PlanPutEndpoint())
api.add_route('/open-source/plans/{id}/delete', plans.PlanDeleteEndpoint())


api.add_route('/open-source/parlours/{id}/consultants/', consultants.ConsultantGetAllEndpoint())
api.add_route('/open-source/parlours/{id}/consultants/pending', consultants.ConsultantGetAllPendingEndpoint())
api.add_route('/open-source/parlours/{id}/consultants/archived', consultants.ConsultantGetAllArchivedEndpoint())
api.add_route('/open-source/consultants', consultants.ConsultantPostEndpoint())
api.add_route('/open-source/consultants/{id}', consultants.ConsultantGetEndpoint())
api.add_route('/open-source/consultants/{id}/update', consultants.ConsultantPutEndpoint())
api.add_route('/open-source/consultants/{id}/change_password', consultants.ConsultantChangePasswordEndpoint())
api.add_route('/open-source/consultants/{id}/delete', consultants.ConsultantDeleteEndpoint())
api.add_route('/open-source/consultants/signin', consultants.ConsultantAuthEndpoint())
api.add_route('/open-source/consultants/signup', consultants.ConsultantSignupEndpoint())
api.add_route('/open-source/consultants/{id}/actions/change_password', consultants.ChangeUserPasswordEndpoint())
api.add_route('/open-source/actions/forgot_password', consultants.ForgotPasswordEndpoint())


api.add_route('/open-source/actions/{id}/export_to_excel/', main_members.ApplicantExportToExcelEndpoint())
api.add_route('/open-source/members/actions/export_to_excel', main_members.FailedMembersExcel())
api.add_route('/open-source/{id}/invoices/actions/export_to_excel', payments.InvoiceExportToExcelEndpoint())
api.add_route('/open-source/actions/download_failed_members/', main_members.DownloadFailedMembers())

api.add_route('/open-source/consultants/{id}/applicants/', applicants.ApplicantGetAllEndpoint())
api.add_route('/open-source/applicants', applicants.ApplicantPostEndpoint())
api.add_route('/open-source/applicants/{id}', applicants.ApplicantGetEndpoint())
api.add_route('/open-source/applicants/{id}/update', applicants.ApplicantPutEndpoint())
api.add_route('/open-source/applicants/{id}/delete', applicants.ApplicantDeleteEndpoint())


api.add_route('/open-source/consultants/{id}/main-members/all', main_members.MainGetAllConsultantEndpoint())
api.add_route('/open-source/consultants/{id}/main-members/archived', main_members.MainGetAllArchivedConsultantEndpoint())
api.add_route('/open-source/parlours/{id}/main-members/all', main_members.MainGetAllParlourEndpoint())
api.add_route('/open-source/parlours/{id}/main-members/archived', main_members.MainGetAllArchivedParlourEndpoint())
api.add_route('/open-source/consultants/{id}/main-members', main_members.MainMemberPostEndpoint())
api.add_route('/open-source/consultants/{id}/actions/import_members', main_members.MainMemberBulkPostEndpoint())
api.add_route('/open-source/main-members/{id}/upload', main_members.MainMemberPostFileEndpoint())
api.add_route('/open-source/parlours/{id}/main-members/file', main_members.MainMemberDownloadCSVGetEndpoint())
api.add_route('/open-source/main-members/{id}/get', main_members.MainMemberGetEndpoint())
api.add_route('/open-source/main-members/{id}/update', main_members.MainMemberPutEndpoint())
api.add_route('/open-source/plans/{id}/check-age-limit', main_members.MainMemberCheckAgeLimitEndpoint())
api.add_route('/open-source/main-members/{id}/exception', main_members.MainMemberPutAgeLimitExceptionEndpoint())
api.add_route('/open-source/main-members/{id}/restore', main_members.MainMemberRestorePutEndpoint())
api.add_route('/open-source/main-members/{id}/delete', main_members.MainMemberDeleteEndpoint())
api.add_route('/open-source/main-members/{id}/archive', main_members.MainMemberArchiveEndpoint())
api.add_route('/open-source/main-members/send-sms', main_members.SMSService())
api.add_route('/open-source/main-members/{id}/document', main_members.MemberCertificateGetEndpoint())
api.add_route('/open-source/main-members/{id}/personal_docs', main_members.MemberPersonalDocsGetEndpoint())

api.add_route('/open-source/applicants/{id}/dependants/all', dependants.DependantMembersGetAllEndpoint())
api.add_route('/open-source/dependants', dependants.DependantPostEndpoint())
# api.add_route('/open-source/dependants/{id}/get', dependants.MainMemberGetEndpoint())
api.add_route('/open-source/dependants/{id}/update', dependants.DependantPutEndpoint())
api.add_route('/open-source/dependants/{id}/delete', dependants.DependantDeleteEndpoint())

api.add_route('/open-source/applicants/{id}/extended-members/all', extended_members.ExtendedMembersGetAllEndpoint())
api.add_route('/open-source/extended-members', extended_members.ExtendedMembersPostEndpoint())
api.add_route('/open-source/extended-members/{id}/get', extended_members.ExtendedMemberGetEndpoint())
api.add_route('/open-source/extended-members/{id}/update', extended_members.ExtendedMemberPutEndpoint())
api.add_route('/open-source/extended-members/{id}/exception', extended_members.ExtendedMemberPutAgeLimitExceptionEndpoint())
api.add_route('/open-source/extended-members/{id}/delete', extended_members.ExtededMemberDeleteEndpoint())
api.add_route('/open-source/extended-members/{id}/promote', extended_members.MainMemberPromoteEndpoint())
api.add_route('/open-source/applicants/{id}/extended-members/age-limit', extended_members.ExtendedMemberCheckAgeLimitEndpoint())

api.add_route('/open-source/applicants/{id}/additional_extended_members/all', additional_extended_members.AdditionalExtendedMembersGetAllEndpoint())
api.add_route('/open-source/additional_extended_members', additional_extended_members.AdditionalExtendedMembersPostEndpoint())
# api.add_route('/open-source/additional_extended_members/{id}/get', extended_members.MainMemberGetEndpoint())
api.add_route('/open-source/additional_extended_members/{id}/update', additional_extended_members.AdditionalExtendedMemberPutEndpoint())
api.add_route('/open-source/additional_extended_members/{id}/delete', additional_extended_members.AdditionalExtendedMemberDeleteEndpoint())

api.add_route('/open-source/applicants/{id}/payments/all', payments.PaymentsGetAllEndpoint())
api.add_route('/open-source/applicants/{id}/payments/last', payments.PaymentGetLastEndpoint())
api.add_route('/open-source/parlours/{id}/payments', payments.PaymentPostEndpoint())

api.add_route('/open-source/applicants/{id}/invoices/all', payments.InvoicesGetAllEndpoint())
api.add_route('/open-source/invoices/{id}', payments.RecieptGetEndpoint())
api.add_route('/open-source/invoice/{id}/delete', payments.InvoiceDeleteEndpoint())


api.add_route('/open-source/admins/signup', admins.AdminSignupEndpoint())

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8009, api)
    httpd.serve_forever()
