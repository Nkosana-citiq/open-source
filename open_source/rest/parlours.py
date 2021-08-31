import falcon
import json
import logging

from open_source import db, utils
from open_source.rest.auth import authenticate_parlour
from open_source.core.parlours import Parlour
from open_source import webtokens


logger = logging.getLogger(__name__)


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


class ParlourGetEndpoint:

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
            # parlour = session.query(Parlour).filter(Parlour.parlour_id == id).first()
            parlour = session.query(Parlour).filter(
                Parlour.parlour_id == id,
                Parlour.state == Parlour.STATE_ACTIVE
            ).first()

            # parlour_id = '{}'.format(parlour.id)

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

    def on_post(self, req, resp):

        with db.transaction() as session:
            errors = {}
            rest_dict = req

            rest_dict['username'] = rest_dict['username'].lower().strip()

            username = rest_dict['username']

            user = Parlour()

            if not Parlour.is_username_unique(session, user.username):
                errors['username'] = 'Username {} is already in use.'.format(
                    user.username)

            if not utils.is_valid_email_address(user.username):
                errors['username'] = 'Username must be a valid email address'

            # if not Parlour.is_email_unique(session, user.username):
            #     errors['username'] = 'Email address {} is already in use.'.format(
            #         user.username)

            if rest_dict["password"] != rest_dict["confirm_password"]:
                errors['password'] = 'Password and confirm Password do not match.'

            if errors:
                raise falcon.HttpValidationError(user.to_rest_errors(errors))

            user.email = username

            # user.role_id = Role.TENANT

            # password = User.generate_password()

            user.set_password(rest_dict["password"])

            session.add(user)

            session.commit()

            user = user.to_dict()

            resp.body = json.dumps({
                'id': user['id'],
                'username': user['username'],
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

                user, success = authenticate_parlour(session, username, password)

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