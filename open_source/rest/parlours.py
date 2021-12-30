from datetime import datetime
import falcon
import json
import logging
import smtplib

from dateutil import parser
from dateutil.relativedelta import relativedelta

from open_source import db, utils
from open_source.core import parlours
from open_source.core.consultants import Consultant
from open_source.core.parlours import Parlour
from open_source import webtokens
from sqlalchemy import Date, cast, func
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from falcon_cors import CORS

logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)


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
                parlour = session.query(Parlour).filter(
                    Parlour.id == id,
                    Parlour.state == Parlour.STATE_ACTIVE
                ).first()
                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")

                resp.body = json.dumps(parlour.to_dict(), default=str)
        except Exception as e:
            logger.exception("Error, Failed to get Parlour with ID {}.".format(id))
            raise e


class ParlourGetAllEndpoint:
    cors = public_cors
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

                search_field = None

                if "search_string" in req.params:
                        search_field = req.params.pop("search_string")
                if search_field:
                    search_date = datetime.strptime(search_field, "%d/%m/%Y")

                    parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ACTIVE).all()

                    parlours = [p for p in parlours if p.created_at.date() == search_date.date()]
                else:
                    parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ACTIVE).all()

                if parlours:
                    resp.body = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.body = json.dumps([])

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

        with db.transaction() as session:
            errors = {}
            rest_dict = json.load(req.bounded_stream)

            if not rest_dict.get('email'):
                raise falcon.HTTPBadRequest(title="Email", description="Email is a required field.")

            if not rest_dict.get('username'):
                raise falcon.HTTPBadRequest(title="Username", description="Username is a required field.")

            rest_dict['email'] = rest_dict['email'].lower().strip()

            email = rest_dict.get('email')

            user = Parlour()

            if not utils.is_valid_email_address(email):
                errors['email'] = 'Email must be a valid email address'
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if not utils.is_email_unique(session, email):
                errors['email'] = 'Email address {} is already in use.'.format(
                    email)
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if rest_dict["password"] != rest_dict["confirm_password"]:
                errors['password'] = 'Password and confirm Password do not match.'
                raise falcon.HTTPBadRequest(title="password", description=errors["password"])

            user.email = email
            user.username = rest_dict.get("username")
            user.parlourname = rest_dict.get("parlour_name")
            user.address = rest_dict.get("address")
            user.personname = rest_dict.get("person_name")
            user.number = rest_dict.get("number")
            user.agreed_to_terms = rest_dict.get("agreed_to_terms")
            user.state = Parlour.STATE_ACTIVE
            user.created_at = datetime.now()
            user.modified_at = datetime.now()

            user.set_password(rest_dict.get("password"))

            session.add(user)

            session.commit()

            user_dict = user.to_dict()

            resp.body = json.dumps(user_dict, default=str)


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
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing email field.")

                parlour = session.query(Parlour).filter(
                    Parlour.id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
            
                parlour.parlourname=req["parlour_name"]
                parlour.personname=req["person_name"]
                parlour.address=req["address"]
                parlour.number=req["number"]
                parlour.email=req["email"]
                parlour.state=Parlour.STATE_ACTIVE
                parlour.save(session)
                resp.body = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTPBadRequest(title="Error",
            description="Processing Failed. experienced error while creating Parlour.")


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
                parlour = session.query(Parlour).filter(Parlour.id == id, Parlour.state != Parlour.STATE_DELETED).first()

                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found", description="Parlour does not exist.")

                parlour.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Parlour with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Parlour with ID {}.".format(id))


class ChangeParlourPasswordEndpoint:
    cors = public_cors
    def on_post(self, req, resp, id):
        with db.transaction() as session:
            parlour = session.query(Parlour).filter(
                Parlour.id == id,
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
            rest_dict = json.load(req.bounded_stream)

            if not rest_dict.get('email'):
                raise falcon.HTTPBadRequest(title="Email", description="Email is a required field.")

            if not rest_dict.get('username'):
                raise falcon.HTTPBadRequest(title="Username", description="Username is a required field.")

            rest_dict['email'] = rest_dict['email'].lower().strip()

            email = rest_dict.get('email')

            user = Parlour()

            if not utils.is_valid_email_address(email):
                errors['email'] = 'Email must be a valid email address'
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if not utils.is_email_unique(session, email):
                errors['email'] = 'Email address {} is already in use.'.format(
                    email)
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if rest_dict["password"] != rest_dict["confirm_password"]:
                errors['password'] = 'Password and confirm Password do not match.'
                raise falcon.HTTPBadRequest(title="password", description=errors["password"])

            user.email = email
            user.username = rest_dict.get("username")
            user.parlourname = rest_dict.get("parlour_name")
            user.address = rest_dict.get("address")
            user.personname = rest_dict.get("person_name")
            user.number = rest_dict.get("number")
            user.agreed_to_terms = rest_dict.get("agreed_to_terms")
            user.state = Parlour.STATE_PENDING
            user.created_at = datetime.now()
            user.modified_at = datetime.now()

            user.set_password(rest_dict.get("password"))

            session.add(user)

            session.commit()

            user_dict = user.to_dict()

            resp.body = json.dumps(user_dict, default=str)


class ParlourGetAllPendingEndpoint:
    cors = public_cors
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
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_PENDING).all()

                if parlours:
                    resp.body = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Parlour for user with ID {}.".format(id))


class ParlourGetAllArchivedEndpoint:
    cors = public_cors
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
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ARCHIVED).all()

                if parlours:
                    resp.body = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
                else:
                    resp.body = json.dumps([])

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
                rest_dict = json.load(req.bounded_stream)

                if 'username' not in rest_dict:
                    raise falcon.HTTPBadRequest(
                        title='400 Malformed Auth request',
                        description='Missing credential[username]')

                username = rest_dict.get('username')

                if 'password' not in rest_dict:
                    raise falcon.HTTPBadRequest(
                        title='400 Malformed Auth request',
                        description='Missing credential[password]'
                    )
                password = rest_dict.get('password')

                user, success = utils.authenticate(session, username, password)

                if success:
                    text = webtokens.create_token_from_parlour(user)

                    if isinstance(user, Parlour):
                        permission = "Parlour"
                    else:
                        permission =  "Consultant" if isinstance(user, Consultant) else "admin"

                    resp.body = json.dumps(
                        {
                            "user": user.to_dict(),
                            "token": text,
                            "permission": permission
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
            print(e)
            raise falcon.HTTPInternalServerError('500 Internal Server Error', 'General Error')


class ForgotPasswordEndpoint:
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

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


class ResetPasswordPostEndpoint:
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        with db.transaction() as session:

            rest_dict = json.load(req.bounded_stream)
            password = rest_dict.get('password')
            email =  rest_dict.get('email')

            if not email:
                raise falcon.HTTPBadRequest(title='Error', description='Failed to identify user.')

            if not password:
                raise falcon.HTTPBadRequest(title='Error', description='Password is required')

            # if not utils.is_valid_password(password):
            #     raise falcon.HTTPBadRequest(title='Error', description='Password is invalid')

            if 'confirm_password' in rest_dict:

                confirm_password = rest_dict.get('confirm_password')

                if confirm_password != password:
                    raise falcon.HTTPBadRequest(title='Error', description='Password and confirm password do not match')

            try:
                reset = session.query(Parlour).filter(Parlour.email == email, Parlour.state == Parlour.STATE_ACTIVE).one_or_none()
            except MultipleResultsFound:
                raise falcon.HTTPBadRequest(title='Error', description='The email for this account is not unique')

            if not reset:
                try:
                    reset = session.query(Consultant).filter(Consultant.email == email, Consultant.state == Consultant.STATE_ACTIVE).one_or_none()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title='Error', description='The email for this account is not unique')
                if not reset:
                    raise falcon.HTTPBadRequest(title='Error', description='Password reset is invalid.')

            # reset the users password
            reset.set_password(password)
            # make the reset deleted so that we cannot use it again

            resp.body = json.dumps({'status': 'success'})


class ParlourSuspendEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        import datetime
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:

                parlour = session.query(Parlour).filter(
                    Parlour.id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
            
                parlour.state=Parlour.STATE_ARCHIVED

                resp.body = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTPBadRequest(title="Error",
            description="Processing Failed. experienced error while creating Parlour.")


class ParlourActivateEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        import datetime
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:

                parlour = session.query(Parlour).filter(
                    Parlour.id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")

                parlour.state=Parlour.STATE_ACTIVE

                resp.body = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTPBadRequest(title="Error",
            description="Processing Failed. experienced error while creating Parlour.")


class ParlourAddSMSEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        import datetime
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(
                    Parlour.id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
                if not parlour.number_of_sms:
                    parlour.number_of_sms = 0
                if req.get("number_of_sms"):
                    parlour.number_of_sms = sum([parlour.number_of_sms, req.get("number_of_sms", 0)])

                resp.body = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTPBadRequest(title="Error",
            description="Processing Failed. experienced error while creating Parlour.")
