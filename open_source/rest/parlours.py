from datetime import datetime
import falcon
import json
import logging

from open_source import db, utils
from open_source.core.parlours import Parlour
from open_source import webtokens
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

logger = logging.getLogger(__name__)


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


def authenticate_parlour_by_username(session, username, password):
    try:
        user = session.query(Parlour).filter(
            Parlour.username == username,
            Parlour.state == Parlour.STATE_ACTIVE
        ).first()
    except NoResultFound:
        user = None

    return user, False if user is None else user.authenticate(password)


def authenticate_parlour_by_email(session, email, password):
    try:
        user = session.query(Parlour).filter(
            Parlour.email == email,
            Parlour.state == Parlour.STATE_ACTIVE
        ).first()
    except NoResultFound:
        user = None

    return user, False if user is None else user.authenticate(password)


class ParlourGetEndpoint:

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
                parlour = session.query(Parlour).filter(
                    Parlour.parlour_id == id,
                    Parlour.state == Parlour.STATE_ACTIVE
                ).first()
                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")

                resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Parlour with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Parlour with ID {}.".format(id))


class ParlourGetAllEndpoint:

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
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ACTIVE).all()

                if parlours:
                    resp.text = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Parlour for user with ID {}.".format(id))


class ParlourPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        import datetime
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                parlour_exists = session.query(Parlour).filter(
                    Parlour.email == req["email"],
                    Parlour.state == Parlour.STATE_ACTIVE).first()

                if not parlour_exists:
                    parlour = Parlour(
                        parlourname=req["parlour_name"],
                        personname=req["person_name"],
                        number=req["number"],
                        email=req["email"],
                        state=Parlour.STATE_ACTIVE,
                    )
                    parlour.save(session)
                    resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class ParlourPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        import datetime
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                parlour = session.query(Parlour).filter(
                    Parlour.parlour_id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
            
                parlour.parlourname=req["parlour_name"],
                parlour.personname=req["person_name"],
                parlour.number=req["number"],
                parlour.email=req["email"],
                parlour.state=Parlour.STATE_ACTIVE,
                parlour.save(session)
                resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class ParlourDeleteEndpoint:

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
                parlour = session.query(Parlour).filter(Parlour.parlour_id == id).first()

                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")
                if parlour.is_deleted:
                    falcon.HTTPNotFound("Parlour does not exist.")

                parlour.delete(session)
                resp.text = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Parlour with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Parlour with ID {}.".format(id))


class ChangeParlourPasswordEndpoint:

    def on_post(self, req, resp, id):
        with db.transaction() as session:
            parlour = session.query(Parlour).filter(
                Parlour.parlour_id == id,
                Parlour.state == Parlour.STATE_ACTIVE
            ).first()


            if parlour.id != id:
                # Currently logged in user should not be able to
                # change other user's passwords unless Super Admin
                raise falcon.HttpValidationError(
                    {'user': 'You may not set another user\'s password'})
            
            if parlour.password != parlour.set_password(req["current_password"]):
                raise falcon.HttpValidationError({"Error": "Password is incorrect"})

            if not req["password"] or not req["confirm_password"]:
                raise falcon.HttpValidationError({"Error": "Missing field(s)"})

            if req["password"] != req["confirm_password"]:
                raise falcon.HttpValidationError({"Error": "Password and confirmpassword must match"})

            parlour.set_password(req['password'])
            session.commit()
            resp.body = json.dumps(parlour.to_dict())


class ParlourSignupEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):

        with db.transaction() as session:
            errors = {}
            rest_dict = get_json_body(req)

            if not rest_dict.get('email'):
                raise falcon.HTTP_BAD_REQUEST(title="Email", description="Email is a required field.")

            if not rest_dict.get('username'):
                raise falcon.HTTP_BAD_REQUEST(title="Username", description="Username is a required field.")

            rest_dict['email'] = rest_dict['email'].lower().strip()

            email = rest_dict.get('email')

            user = Parlour()

            if not Parlour.is_username_unique(session, rest_dict.get("username")):
                errors['username'] = 'Username {} is already in use.'.format(
                    user.username)

            if not utils.is_valid_email_address(email):
                errors['email'] = 'Email must be a valid email address'

            if not Parlour.is_email_unique(session, email):
                errors['email'] = 'Email address {} is already in use.'.format(
                    email)

            if rest_dict["password"] != rest_dict["confirm_password"]:
                errors['password'] = 'Password and confirm Password do not match.'

            if errors:
                raise falcon.HTTPBadRequest(errors)

            user.email = email
            user.parlourname = rest_dict.get("parlour_name")
            user.personname = rest_dict.get("person_name")
            user.number = rest_dict.get("number")
            user.state = Parlour.STATE_ACTIVE
            user.created_at = datetime.now()
            user.modified_at = datetime.now()

            user.set_password(rest_dict.get("password"))

            session.add(user)

            session.commit()

            user_dict = user.to_dict()

            resp.body = json.dumps({
                'id': user_dict['id'],
                'email': user_dict.get('email'),
            })


class ParlourGetAllPendingEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_PENDING).all()

                if parlours:
                    resp.text = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Parlour for user with ID {}.".format(id))


class ParlourGetAllArchivedEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ARCHIVED).all()

                if parlours:
                    resp.text = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Parlour for user with ID {}.".format(id))


class ParlourAuthEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        try:
            with db.transaction() as session:
                rest_dict = req.media

                if 'email' in rest_dict:
                    # CIC Wholesaler password reset
                    email = rest_dict.get('email')

                if 'username' in rest_dict:
                    # Citiq Prepaid password reset
                    username = rest_dict.get('user_identifier')

                email = rest_dict.get('email')
                if not rest_dict.get("email") and not rest_dict.get("username"):
                    raise falcon.HTTPBadRequest(
                        title='400 Malformed Auth request',
                        description='Missing credential[username]'
                    )

                password = rest_dict.get('password')
                if not password:
                    raise falcon.HTTPBadRequest(
                        title='400 Malformed Auth request',
                        description='Missing credential[password]'
                    )

                if rest_dict.get('email'):
                    user, success = authenticate_parlour_by_email(session, email, password)
                else:
                    user, success = authenticate_parlour_by_username(session, username, password)
                
                if success:
                    text = webtokens.create_token_from_parlour(user)

                    resp.body = json.dumps(
                        {
                            'user': user.to_dict(),
                            "token": text,
                            "permission": "parlour"
                        }, default=str)
                else:
                    raise falcon.HTTPUnauthorized(
                        title='401 Authentication Failed',
                        description='The credentials provided are not valid',
                        headers={}
                        )

        except (falcon.HTTPBadRequest, falcon.HTTPUnauthorized):
            raise
        except json.decoder.JSONDecodeError as e:
            raise falcon.HTTPBadRequest('400 Malformed Json', str(e))
        except Exception as e:
            raise falcon.HTTPInternalServerError('500 Internal Server Error', 'General Error')


class ForgotPasswordEndpoint:

    def on_post(self, req, resp):

        with db.transaction() as session:

            rest_dict = req

            email = None

            user_identifier = None

            user = None

            if 'email' in rest_dict:
                email = rest_dict.get('email')

            if not email and not user_identifier:
                raise falcon.HttpValidationError({'email': 'An email address or username is required'})

            # if email and not user_identifier:
            user = self.get_user_by_email(session, email)
            if not user:
                raise falcon.HttpValidationError({
                    'email': 'Invalid email address or more than one account is linked to this email'
                })

            session.add(user)
            session.commit()

            resp.body = json.dumps({'status': 'success'})


    def get_user_by_email(self, session, email):
        try:
            return session.query(Parlour)\
                .filter(Parlour.email == email, Parlour.state == Parlour.STATE_ACTIVE).one()
        except MultipleResultsFound:
            return None
        except NoResultFound:
            return None
        return None


# class ResetPasswordPostEndpoint:

#     def on_post(self, req, resp):
#         with db.transaction() as session:

#             rest_dict = get_json_body(req)
#             code = rest_dict.get('code')
#             password = rest_dict.get('password')

#             if not password:
#                 raise falcon.HttpValidationError({'password': 'Password is required'})

#             if not utils.is_valid_password(password):
#                 raise falcon.HttpValidationError({'password': 'Password is invalid'})

#             # Non CIC users must confirm their new password -
#             # CIC user password confirmation handled by CIC Web
#             if 'confirm_password' in rest_dict:

#                 confirm_password = rest_dict.get('confirm_password')

#                 if confirm_password != password:
#                     raise falcon.HttpValidationError({'password': 'Password and confirm password do not match'})

#             reset = get_password_reset(session, code)

#             if not reset:
#                 raise exceptions.HttpValidationError({'code': 'Password reset is invalid or has expired'})

#             if reset.is_deleted():
#                 raise exceptions.HttpValidationError({'code': 'Password reset is already used'})

#             # reset the users password
#             reset.user.set_password(password)
#             # make the reset deleted so that we cannot use it again
#             reset.make_deleted()

#             resp.body = json.dumps({'status': 'success'})

#     def swagger_path(self):
#         return {
#             "description": "Reset a users password",
#             "operationId": "resetPassword",
#             "parameters": [
#                 SwaggerHelper.object_parameter(
#                     'ResetPasswordRequest', _in='body')
#             ],
#             "responses": {
#                 "200": SwaggerHelper.response_200('Status'),
#                 "default": SwaggerHelper.response_default()
#             }
#         }

#     def swagger_definition(self):
#         doc = SwaggerHelper.object_with_properties('ResetPasswordRequest', {
#             'code': {'type': 'string'},
#             'password': {'type': 'string'}
#         })

#         doc.update(SwaggerHelper.object_with_properties('Status', {
#             'status': {'type': 'string', 'description': 'The status in text'}
#         }))
#         return doc
