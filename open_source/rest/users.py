from datetime import datetime
import falcon
import json

from sqlalchemy.sql.elements import or_

from open_source import db, utils
from open_source.core.parlours import Parlour
from open_source.core.roles import Role
from open_source.core.users import User
from open_source import webtokens
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from falcon_cors import CORS
import logging


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


class AuthEndpoint:
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

                    resp.body = json.dumps(
                        {
                            "user": user.to_dict(),
                            "token": text,
                            "permission": user.role.name
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


class UserSignupEndpoint:

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

            user = User()

            if not utils.is_username_unique(session, rest_dict.get("username")):
                errors['username'] = 'Username {} is already in use.'.format(
                    user.username)
                raise falcon.HTTPBadRequest(title="Username", description=errors["usename"])
            if not utils.is_valid_email_address(email):
                errors['email'] = 'Email must be a valid email address'
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if not utils.is_email_unique(session, email):
                errors['email'] = 'Email address {} is already in use.'.format(
                    email)
                raise falcon.HTTPBadRequest(title="Email", description=errors["email"])

            if not rest_dict["password"]:
                errors['password'] = 'Password is a required field.'
                raise falcon.HTTPBadRequest(title="password", description=errors["password"])

            user.email = email
            user.username = rest_dict.get("username")
            user.first_name = rest_dict.get("first_name")
            user.last_name = rest_dict.get("last_name")
            user.number = rest_dict.get("number")
            user.state = User.STATE_ACTIVE
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


class UserDeleteEndpoint:

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
                user = session.query(User).filter(User.id == id).first()

                if user is None:
                    raise falcon.HTTPNotFound(title="User Not Found")
                if user.is_deleted:
                    falcon.HTTPNotFound("User does not exist.")

                user.delete(session)
                resp.body = json.dumps({})
        except:
            logger.exception("Error, Failed to delete User with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete User with ID {}.".format(id))

class ConsultantGetAllEndpoint:
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
                    Parlour.state == Parlour.STATE_ACTIVE,
                    Parlour.id == id).one_or_none()

                if not parlour:
                    raise falcon.HTTPBadRequest(title="Error", description="Failed to get parlour with give ID")

                users = session.query(User).filter(
                    User.state == User.STATE_ACTIVE,
                    User.parlour_id == parlour.id,
                    User.role_id == Role.IS_CONSULTANT
                ).all()

                if users:
                    resp.body = json.dumps([user.to_dict() for user in users], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get User for Parlour with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))
