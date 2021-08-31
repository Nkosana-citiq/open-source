from datetime import datetime
from open_source.rest.auth import authenticate_consultant
import falcon
import json
import logging

from open_source import db, utils

from open_source.core.consultants import Consultant
from open_source.core.parlours import Parlour
from open_source import webtokens
logger = logging.getLogger(__name__)


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


class ConsultantGetEndpoint:

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                consultant = session.query(Consultant).filter(
                    Consultant.consultant_id == id,
                    Consultant.state == Consultant.STATE_ACTIVE
                ).first()
                if consultant is None:
                    raise falcon.HTTPNotFound(title="Consultant Not Found")

                resp.text = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Consultant with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant with ID {}.".format(id))


class ConsultantGetAllEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                consultants = session.query(Consultant).filter(Consultant.state == Consultant.STATE_ACTIVE).all()

                if consultants:
                    resp.text = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))


class ConsultantPostEndpoint:

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                consultant_exists = session.query(Consultant).filter(
                    Consultant.email == req["email"],
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if consultant_exists:
                    raise falcon.HTTP_BAD_REQUEST("Email already exists. Email must be unique")

                consultant_exists = session.query(Consultant).filter(
                    Consultant.first_name == req["first_name"],
                    Consultant.last_name == req["last_name"],
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if consultant_exists:
                    raise falcon.HTTP_BAD_REQUEST("First name and last name fields already exist")

                consultant = Consultant(
                    first_name = req['first_name'],
                    last_name = req['last_name'],
                    email = req['email'],
                    branch = req['branch'],
                    number = req['number'],
                    parlour_id = req["parlour_id"],
                    state=Consultant.STATE_ACTIVE,
                )
                consultant.save(session)
                resp.text = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Consultant.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Consultant.")


class ConsultantPutEndpoint:

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                consultant = session.query(Consultant).filter(
                    Consultant.consultant_id == id).first()

                if not consultant:
                    raise falcon.HTTPNotFound(title="Consultant not found", description="Could not find consultant with given ID.")

                consultant.first_name = req['first_name']
                consultant.last_name = req['last_name']
                consultant.email = req['email']
                consultant.branch = req['branch']
                consultant.number = req['number']
                consultant.save(session)
                resp.text = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Consultant.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Consultant.")


class ConsultantDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                consultant = session.query(Consultant).filter(Consultant.parlour_id == id).first()

                if consultant is None:
                    raise falcon.HTTPNotFound(title="Consultant Not Found")
                if consultant.is_deleted:
                    falcon.HTTPNotFound("Consultant does not exist.")

                consultant.delete(session)
                resp.text = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete Consultant with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Consultant with ID {}.".format(id))


class ChangeUserPasswordEndpoint:

    def on_post(self, req, resp, id):
        with db.transaction() as session:
            # parlour = session.query(Parlour).filter(Parlour.parlour_id == id).first()
            consultant = session.query(Consultant).filter(
                Consultant.consultant_id == id,
                Consultant.state == Consultant.STATE_ACTIVE
            ).first()

            # parlour_id = '{}'.format(parlour.id)

            if consultant.id != id:
                # Currently logged in user should not be able to
                # change other user's passwords unless Super Admin
                raise falcon.HttpValidationError(
                    {'user': 'You may not set another user\'s password'})
            
            if consultant.password != consultant.set_password(req["current_password"]):
                raise falcon.HttpValidationError({"Error": "Password is incorrect"})

            if not req["password"] or not req["confirm_password"]:
                raise falcon.HttpValidationError({"Error": "Missing field(s)"})

            if req["password"] != req["confirm_password"]:
                raise falcon.HttpValidationError({"Error": "Password and confirmpassword must match"})

            consultant.set_password(req['password'])
            session.commit()
            resp.body = json.dumps(consultant.to_dict())


class ConsultantSignupEndpoint:

    def on_post(self, req, resp):

        with db.transaction() as session:
            errors = {}
            rest_dict = req
            parlour = session.query(Parlour).filter(
                Parlour.parlour_id == rest_dict["parlour_id"],
                Parlour.state == Parlour.STATE_ACTIVE
            ).first()

            if not parlour:
                raise falcon.HTTPUnauthorized(title="Missing Parlour", description="Parlour does not exist")

            rest_dict['username'] = rest_dict['username'].lower().strip()

            username = rest_dict['username']

            user = Consultant()

            if not Consultant.is_username_unique(session, user.username):
                errors['username'] = 'Username {} is already in use.'.format(
                    user.username)

            if not utils.is_valid_email_address(user.username):
                errors['username'] = 'Username must be a valid email address'

            if not Consultant.is_email_unique(session, user.username):
                errors['username'] = 'Email address {} is already in use.'.format(
                    user.username)

            if rest_dict["password"] != rest_dict["confirm_password"]:
                errors['password'] = 'Password and confirm Password do not match.'

            if errors:
                raise falcon.HTTPBadRequest(errors)

            user.email = username
            user.first_name=req["first_name"],
            user.last_name=req["last_name"],
            user.state=Consultant.STATE_ACTIVE,
            user.branch=req["branch"],
            user.number=req["number"],
            user.modified=datetime.now(),
            user.created=datetime.now(),
            user.parlour_id=req["parlour_id"]
            # user.role_id = Role.TENANT

            # password = User.generate_password()

            user.set_password(rest_dict["password"])

            session.add(user)

            user.save(session)

            user = user.to_dict()

            resp.body = json.dumps({
                'id': user['id'],
                'username': user['username'],
            })



class ConsultantGetAllPendingEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                consultants = session.query(Consultant).filter(Consultant.state == Consultant.STATE_PENDING).all()

                if consultants:
                    resp.text = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))



class ConsultantGetAllArchivedEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                consultants = session.query(Consultant).filter(Consultant.state == Consultant.STATE_ARCHIVED).all()

                if consultants:
                    resp.text = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.text = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))


class ConsultantAuthEndpoint:

    def on_post(self, req, resp):
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
                            'user': user.to_dict(),
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
            raise falcon.HTTPBadRequest('400 Malformed Json', str(e))
        except Exception as e:
            raise falcon.HTTPInternalServerError('500 Internal Server Error', 'General Error')
