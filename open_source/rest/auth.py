import json
import datetime

import falcon

# from citiq_rest import exceptions

from open_source import db, webtokens, utils, config, rest
# from admin_service.core import audit
# from admin_service.core.emailq import EmailQueue
# from admin_service.core.one_time_pins import OneTimePin
from open_source.core.consultants import Consultant
from open_source.core.parlours import Parlour


from open_source.rest import endpoints, raise_malformed_json_exception,\
    raise_general_exception, get_json_body, handle_metrics, handle_errors
from admin_service.rest.endpoints import SwaggerHelper

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

conf = config.get_config()
# audit_log_client = audit.get_audit_log_client()


def authenticate_consultant(session, username, password):
    consultant = session.query(Consultant)\
        .filter(
            Consultant.username == username,
            Consultant.state == Consultant.STATE_ACTIVE
    ).one_or_none()

    if consultant and not consultant.can_login():
        return consultant, False
    return consultant, False if consultant is None else consultant.authenticate(password)

def authenticate_parlour(session, username, password):
    user = session.query(Parlour)\
        .filter(
            Parlour.username == username,
            Parlour.state == Parlour.STATE_ACTIVE
    ).one_or_none()

    if user and not user.can_login():
        return user, False
    return user, False if user is None else user.authenticate(password)


# def authenticate_admin(session, username, password):
#     user = session.query(User)\
#         .filter(
#             User.username == username,
#             User.state == User.STATE_ACTIVE
#     ).one_or_none()

#     if user and not user.can_login():
#         return user, False
#     return user, False if user is None else user.authenticate(password)


# def write_audit_log(user, session):
#     from admin_service.core import audit

    # # TODO: Deprecate old audit logs
    # audit.AuditLogClient.save_log(
    #     session,
    #     user,
    #     "admin.users.authenticate",
    #     user.id,
    #     user.salutation,
    #     data_classname=User.__name__
    # )



class AuthEndpoint:

    method = 'POST'

    def post(self, req, resp):
        try:
            with db.transaction() as session:
                rest_dict = get_json_body(req)
                username = rest_dict.get('username')
                if not username:
                    raise falcon.HTTPBadRequest(
                        '400 Malformed Auth request',
                        'Missing credential[username]'
                    )

                password = rest_dict.get('password')
                if not password:
                    raise falcon.HTTPBadRequest(
                        '400 Malformed Auth request',
                        'Missing credential[password]'
                    )

                user, success = authenticate_consultant(session, username, password)

                if success:
                    # write_audit_log(user, session)
                    text = webtokens.create_token_from_consultant(user)
                    resp.body = json.dumps(
                        {
                            'user': user.to_rest_dict(),
                            'token': text.decode('utf-8')
                        })
                else:
                    raise falcon.HTTPUnauthorized(
                        '401 Authentication Failed',
                        'The credentials provided are not valid',
                        {})

        except (falcon.HTTPBadRequest, falcon.HTTPUnauthorized):
            raise
        except json.decoder.JSONDecodeError as e:
            raise_malformed_json_exception(e)
        except Exception as e:
            raise_general_exception(e)

    def swagger_path(self):
        return {
            "description": "Authorize a user",
            "operationId": "authUser",
            "parameters": [
                SwaggerHelper.object_parameter('AuthRequest', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200('AuthResponse'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('AuthRequest', {
            'username': {'type': 'string'},
            'password': {'type': 'string'}
        })
        doc.update(SwaggerHelper.object_with_properties('AuthResponse', {
            'user': {'$ref': '#/definitions/User'},
            'token': {'type': 'string', 'description': 'A JWT token'}
        }))
        return doc


def resource():
    return endpoints.Resource(endpoints=[AuthEndpoint()], secure=False)


class SendOtpEndpoint(endpoints.Endpoint):

    method = 'POST'
    permission = 'admin.meters.view'

    @rest.handle_errors
    @rest.handle_metrics
    def __call__(self, req, resp, id):
        with db.transaction() as session:
            user = rest.get_user(session, req)
            rest_dict = rest.get_json_body(req)
            msisdn = rest_dict.get('msisdn')
            if not msisdn:
                raise exceptions.HttpValidationError({'msisdn': 'Missing field msisdn is required'})

            new_otp = OneTimePin.create_new_pin(session, user.id, msisdn)

            audit_log_client.create_log(
                user,
                "OTP has been requested for user {} {}"
                .format(user.first_name, user.last_name),
                self.permission,
                log_type=audit.AUDITLOGTYPES.SYSTEM_EVENT,
                data_type=DATATYPES.USER
            )

        OneTimePin.sms_otp(new_otp, msisdn)
        resp.body = json.dumps({
            "otp": "sent"
        })

    def swagger_path(self):
        return {
            "description": "Send an OTP to the supplied MSISDN",
            "operationId": "sendOTP",
            "parameters": [
                SwaggerHelper.id_parameter('User', _in='path'),
                SwaggerHelper.object_parameter('Msisdn', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200("OTP Response"),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('Msisdn', {
            "msisdn": {"type": "string"}
        })

        doc.update(SwaggerHelper.object_with_properties('OTP Response', {
            "otp": {"type": "string"},
        }))
        return doc


def send_otp_resource():
    return SendOtpEndpoint().as_resource()


class VerifyOtpEndpoint(endpoints.Endpoint):

    method = 'POST'
    permission = 'admin.meters.view'

    @rest.handle_errors
    @rest.handle_metrics
    def __call__(self, req, resp, id):
        with db.transaction() as session:
            user = rest.get_user(session, req)
            rest_dict = rest.get_json_body(req)
            otp = rest_dict.get('otp')
            if not otp:
                raise exceptions.HttpValidationError({'otp': 'OTP is required'})
            msisdn = rest_dict.get('msisdn')
            if not msisdn:
                raise exceptions.HttpValidationError({'msisdn': 'MSISDN is required'})

            if OneTimePin.verify_pin(session, user.id, msisdn, otp):
                user.cell = msisdn
                resp.body = json.dumps({"verified": "true"})

                audit_log_client.create_log(
                    user,
                    "OTP has been verified for user {} {}"
                    .format(user.first_name, user.last_name),
                    self.permission,
                    log_type=audit.AUDITLOGTYPES.SYSTEM_EVENT,
                    data_type=DATATYPES.USER
                )

            else:
                raise exceptions.ApplicationError('OTP Verification Failed')

    def swagger_path(self):
        return {
            "description": "Verify a supplied OTP",
            "operationId": "verifyOTP",
            "parameters": [
                SwaggerHelper.id_parameter('User', _in='path'),
                SwaggerHelper.object_parameter('OneTimePin', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200("OTP Response"),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        return SwaggerHelper.object_with_properties('OneTimePin', {
            "otp": {"type": "string"}
        })


def verify_otp_resource():
    return VerifyOtpEndpoint().as_resource()


class ForgotPasswordEndpoint(endpoints.Endpoint):

    method = 'POST'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):

        with db.transaction() as session:

            rest_dict = get_json_body(req)

            email = None

            user_identifier = None

            user = None

            if 'email' in rest_dict:
                # CIC Wholesaler password reset
                email = rest_dict.get('email')

            if 'user_identifier' in rest_dict:
                # Citiq Prepaid password reset
                user_identifier = rest_dict.get('user_identifier')

            if not email and not user_identifier:
                raise exceptions.HttpValidationError({'email': 'An email address or username is required'})

            if email and not user_identifier:
                user = self.get_user_by_email(session, email)
                if not user:
                    raise exceptions.HttpValidationError({
                        'email': 'Invalid email address or more than one account is linked to this email'
                    })

            if user_identifier and not email:
                user = self.get_user_by_username(session, user_identifier)
                if not user:
                    user = self.get_user_by_email(session, user_identifier)
                    if not user:
                        raise exceptions.HttpValidationError({'user_identifier': 'Invalid username or email address'})

                # Speedpay, Speedpay admin and voucher manager users cannot log in to vendsystem
                if user.role.id in [6, 7, 14]:
                    raise exceptions.HttpValidationError({'user_identifier': 'Invalid username or email address'})
                email = user.email
                if not email:
                    raise exceptions.HttpValidationError({'email': 'Invalid user email. Please update your email address'})

            if not user.can_login():
                raise exceptions.HttpValidationError(
                    {'user_activation': 'Request not completed. Kindly contact our call centre for assistance.'}
                )

            # if a wholesaler then they must have completed registration
            if user.is_wholesaler() and not user.wholesaler.has_completed_registration(email):
                raise exceptions.HttpValidationError({
                    'email': 'Invalid email or more than one account is linked to this email'
                })

            # email from rest_dict if CIC Wholesaler user else user.email
            email_address = email if email else user.email

            reset = PasswordReset(
                user=user,
                email=email_address,
                code=utils.random_text(20),
                expired=datetime.datetime.now() + datetime.timedelta(days=1)
            )
            session.add(reset)
            session.commit()

            if conf.cic['send_wholesaler_password_reset_email']:
                EmailQueue.enqueue_password_reset_email(session, reset)

            resp.body = json.dumps({'status': 'success'})

            audit_log_client.create_log(
                user,
                "Forgot password request for User: {} {}"
                .format(user.first_name, user.last_name),
                self.permission,
                data_type=DATATYPES.USER,
                log_type=audit.AUDITLOGTYPES.SYSTEM_EVENT
            )

    def swagger_path(self):
        return {
            "description": "Creates a password reset",
            "operationId": "forgotPassword",
            "parameters": [
                SwaggerHelper.object_parameter(
                    'ForgotPasswordRequest', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200('PasswordReset'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('ForgotPasswordRequest', {
            'email': {
                'type': 'string',
                'description': 'user email address'
            }
        })

        doc.update(SwaggerHelper.object_with_properties('PasswordReset', {
            'code': {
                'type': 'string',
                'description': 'A code to access the password reset'
            },
            'expired': {
                'type': 'string',
                'description': 'when the password reset will expire'
            },
            'email': {
                'type': 'string',
                'description': 'email address associated with password reset'
            }
        }))
        return doc

    def get_user_by_email(self, session, email):
        try:
            return session.query(User)\
                .filter(User.email == email, User.state == 1).one()
        except MultipleResultsFound:
            return None
        except NoResultFound:
            return None
        return None

    def get_user_by_username(self, session, username):
        try:
            return session.query(User)\
                .filter(User.username == username, User.state == 1).one()
        except MultipleResultsFound:
            return None
        except NoResultFound:
            return None
        return None


def forgot_password_resource():
    return endpoints.Resource(
        endpoints=[ForgotPasswordEndpoint()],
        secure=False,
        basic_secure=True)


def get_password_reset(session, code):
    try:
        return session.query(PasswordReset)\
            .filter(
                PasswordReset.code == code,
                PasswordReset.expired > datetime.datetime.now()
            ).one()

    except MultipleResultsFound:
        return None
    except NoResultFound:
        return None
    return None


class ResetPasswordPostEndpoint(endpoints.Endpoint):

    method = 'POST'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):
        with db.transaction() as session:

            rest_dict = get_json_body(req)
            code = rest_dict.get('code')
            password = rest_dict.get('password')

            if not password:
                raise exceptions.HttpValidationError({'password': 'Password is required'})

            if not utils.is_valid_password(password):
                raise exceptions.HttpValidationError({'password': 'Password is invalid'})

            # Non CIC users must confirm their new password -
            # CIC user password confirmation handled by CIC Web
            if 'confirm_password' in rest_dict:

                confirm_password = rest_dict.get('confirm_password')

                if confirm_password != password:
                    raise exceptions.HttpValidationError({'password': 'Password and confirm password do not match'})

            reset = get_password_reset(session, code)

            if not reset:
                raise exceptions.HttpValidationError({'code': 'Password reset is invalid or has expired'})

            if reset.is_deleted():
                raise exceptions.HttpValidationError({'code': 'Password reset is already used'})

            # reset the users password
            reset.user.set_password(password)
            # make the reset deleted so that we cannot use it again
            reset.make_deleted()

            resp.body = json.dumps({'status': 'success'})

    def swagger_path(self):
        return {
            "description": "Reset a users password",
            "operationId": "resetPassword",
            "parameters": [
                SwaggerHelper.object_parameter(
                    'ResetPasswordRequest', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200('Status'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('ResetPasswordRequest', {
            'code': {'type': 'string'},
            'password': {'type': 'string'}
        })

        doc.update(SwaggerHelper.object_with_properties('Status', {
            'status': {'type': 'string', 'description': 'The status in text'}
        }))
        return doc


class ResetPasswordGetEndpoint(endpoints.Endpoint):

    method = 'GET'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):
        with db.transaction() as session:

            code = req.params.get('code')

            reset = get_password_reset(session, code)

            if not reset:
                raise exceptions.HttpValidationError({'code': 'Password reset is invalid or has expired'})

            if reset.is_deleted():
                raise exceptions.HttpValidationError({'code': 'Password reset is already used'})

            resp.body = json.dumps({'id': reset.id, 'code': code})

    def swagger_path(self):
        return {
            "description": "Reset a users password",
            "operationId": "resetPassword",
            "responses": {
                "200": SwaggerHelper.response_200('ResetPassword'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('ResetPassword', {
            'id': {'type': 'number'},
            'code': {'type': 'string'}
        })
        return doc


def reset_password_resource():
    return endpoints.Resource(endpoints=[
        ResetPasswordGetEndpoint(),
        ResetPasswordPostEndpoint()],
        secure=False, basic_secure=True)


def get_wholesaler_registration(session, code):
    try:
        return session.query(WholesalerRegistration)\
            .filter(WholesalerRegistration.code == code).one()
    except MultipleResultsFound:
        return None
    except NoResultFound:
        return None
    return None


def get_latest_wholesaler_registration_(session, wholesaler_id):
    return session.query(WholesalerRegistration)\
        .filter(WholesalerRegistration.wholesaler_id == wholesaler_id)\
        .order_by(WholesalerRegistration.id.desc())\
        .first()


def get_wholesaler(session, req, id):
    return rest.get_entity(session, req, Wholesaler, id)


class WholesalerSignupPostEndpoint(endpoints.Endpoint):

    method = 'POST'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):
        with db.transaction() as session:

            rest_dict = get_json_body(req)
            code = rest_dict.get('code')
            password = rest_dict.get('password')

            if not password:
                raise exceptions.HttpValidationError({'password': 'Password is required'})

            if not utils.is_valid_password(password):
                raise exceptions.HttpValidationError({'password': 'Password is invalid'})

            reg = get_wholesaler_registration(session, code)

            if not reg:
                raise exceptions.HttpValidationError({'code': 'Registration is invalid'})

            if reg.is_completed():
                raise exceptions.HttpValidationError({'code': 'Registration has already been completed'})

            wholesaler = session.query(Wholesaler).filter(
                Wholesaler.id == reg.wholesaler_id).one()

            if wholesaler:
                if wholesaler.has_completed_registration(reg.user.email):
                    raise exceptions.HttpValidationError({'code': 'At least one registration has been completed'})

            if reg.is_expired():
                raise exceptions.HttpValidationError({'code': 'Registration has expired'})

            # reset the users password
            reg.user.set_password(password)

            reg.completed = datetime.datetime.now()

            # set wholesaler state to active
            wholesaler.make_active()

            resp.body = json.dumps({'status': 'success'})

    def swagger_path(self):
        return {
            "description": "Reset a users password",
            "operationId": "resetPassword",
            "parameters": [
                SwaggerHelper.object_parameter(
                    'CompleteRegistrationRequest', _in='body')
            ],
            "responses": {
                "200": SwaggerHelper.response_200('Status'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('CompleteRegistrationRequest', {
            'code': {'type': 'string'},
            'password': {'type': 'string'}
        })

        doc.update(SwaggerHelper.object_with_properties('Status', {
            'status': {'type': 'string', 'description': 'The status in text'}
        }))
        return doc


class WholesalerSignupGetEndpoint(endpoints.Endpoint):

    method = 'Get'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):
        with db.transaction() as session:

            code = req.params.get('code')

            reg = get_wholesaler_registration(session, code)

            if not reg:
                raise exceptions.HttpValidationError({'code': 'Registration is invalid'})

            if reg.is_completed():
                raise exceptions.HttpValidationError({'code': 'Registration has already been completed'})

            wholesaler = session.query(Wholesaler).filter(
                Wholesaler.id == reg.wholesaler_id).one()

            if wholesaler and not wholesaler.is_cic_wholesaler:
                raise exceptions.HttpValidationError({'code': 'Not a CIC Wholesaler'})

            if wholesaler and wholesaler.has_completed_registration(reg.user.email):
                raise exceptions.HttpValidationError({'code': 'At least one registration has been completed'})

            if reg.is_expired():
                raise exceptions.HttpValidationError({'code': 'Registration has expired'})

            resp.body = json.dumps(reg.to_rest_dict())

    def swagger_path(self):
        return {
            "description": "Get wholesaler signup",
            "operationId": "getWholesalerSignup",
            "responses": {
                "200": SwaggerHelper.response_200('WholesalerSignup'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('WholesalerSignup', {
            'code': {'type': 'string'},
            'id': {'type': 'number'},
            'user': SwaggerHelper.object_with_properties('User', {
                'id': {'type': 'number'},
                'username': {'type': 'string'}
            })
        })
        return doc


def wholesaler_signup_resource():
    return endpoints.Resource(endpoints=[
        WholesalerSignupGetEndpoint(),
        WholesalerSignupPostEndpoint()],
        secure=False, basic_secure=True)


class WholesalerSignupResendForCodePostEndpoint(endpoints.Endpoint):

    method = 'POST'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp):
        with db.transaction() as session:

            rest_dict = get_json_body(req)

            code = rest_dict.get('code')

            reg = get_wholesaler_registration(session, code)

            if not reg:
                raise exceptions.HttpValidationError({'code': 'Registration is invalid'})

            if reg.is_completed():
                raise exceptions.HttpValidationError({'code': 'Registration has already been completed'})

            wholesaler = session.query(Wholesaler).filter(
                Wholesaler.id == reg.wholesaler_id).one()

            if not wholesaler.is_cic_wholesaler:
                raise exceptions.HttpValidationError({'code': 'Not a CIC Wholesaler'})

            if wholesaler and wholesaler.has_completed_registration():
                raise exceptions.HttpValidationError({'code': 'At least one registration has been completed'})

            if reg.is_expired():
                new_reg = wholesaler.create_registration(reg.user)
                wholesaler.registrations.append(new_reg)
                session.commit()
                if conf.cic['send_wholesaler_registration_email']:
                    EmailQueue.enqueue_wholesaler_registration_email(
                        session, new_reg)
            else:
                raise exceptions.HttpValidationError({'code': 'Registration has not expired'})

            resp.body = json.dumps({'status': 'success'})

    def swagger_path(self):
        return {
            "description": "Creates a new Wholesaler signup from an expired signup",
            "operationId": "postWholesalerSignupResend",
            "parameters": [SwaggerHelper.object_parameter('WholesalerSignupResend', _in='body')],
            "responses": {
                "200": SwaggerHelper.response_200('Status'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('WholesalerSignupResend', {
            'code': {'type': 'string'}
        })

        doc.update(SwaggerHelper.object_with_properties('Status', {
            'status': {'type': 'string', 'description': 'The status in text'}
        }))
        return doc


def wholesaler_signup_resend_for_code_resource():
    return endpoints.Resource(endpoints=[WholesalerSignupResendForCodePostEndpoint()],
                              secure=False, basic_secure=True)


class WholesalerSignupResendPostEndpoint(endpoints.Endpoint):

    method = 'POST'
    permission = 'admin.wholesalers.edit'

    @handle_errors
    @handle_metrics
    def __call__(self, req, resp, id):

        with db.transaction() as session:

            wholesaler = get_wholesaler(session, req, id)

            if wholesaler and wholesaler.has_completed_registration():
                raise exceptions.HttpValidationError({'code': 'At least one registration has been completed'})

            if wholesaler and not wholesaler.is_cic_wholesaler:
                raise exceptions.HttpValidationError({'code': 'Not a CIC Wholesaler'})

            reg = get_latest_wholesaler_registration_(session, wholesaler.id)

            if not reg:
                raise exceptions.HttpValidationError({'code': 'No registrations found for this Wholesaler'})

            if reg.is_expired():
                new_reg = wholesaler.create_registration(reg.user)
                wholesaler.registrations.append(new_reg)
                session.commit()
                if conf.cic['send_wholesaler_registration_email']:
                    EmailQueue.enqueue_wholesaler_registration_email(
                        session, new_reg)
            else:
                if conf.cic['send_wholesaler_registration_email']:
                    EmailQueue.enqueue_wholesaler_registration_email(
                        session, reg)

            resp.body = json.dumps({'status': 'success'})

    def swagger_path(self):
        return {
            "description": "Resend Wholesaler signup email to the supplied Wholesaler",
            "operationId": "postWholesalerSignupIncompleteResend",
            "parameters": [SwaggerHelper.id_parameter('Wholesaler', _in='path')],
            "responses": {
                "200": SwaggerHelper.response_200('Status'),
                "default": SwaggerHelper.response_default()
            }
        }

    def swagger_definition(self):
        doc = SwaggerHelper.object_with_properties('WholesalerSignupIncompleteResend', {
            'id': {'type': 'number'}
        })

        doc.update(SwaggerHelper.object_with_properties('Status', {
            'status': {'type': 'string', 'description': 'The status in text'}
        }))
        return doc


def wholesaler_signup_resend_resource():
    return WholesalerSignupResendPostEndpoint().as_resource()


class VerifyAuthEndpoint(endpoints.Endpoint):
    """
        Verifies the authorization of a user using their token.
        Returns 401 if token bad.
        Else returns User information
    """

    method = 'GET'

    def __call__(self, req, resp):
        with db.no_transaction() as session:
            user = rest.get_user(session, req)

            resp.body = json.dumps(user.to_rest_dict())


def verify_auth_resource():
    return VerifyAuthEndpoint().as_resource()
