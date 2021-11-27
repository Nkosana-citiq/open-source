from datetime import datetime
import dateutil.relativedelta

import falcon
from falcon_cors import CORS
import json
import logging
import smtpd

from open_source import db, utils

from open_source.core.consultants import Consultant
from open_source.core.parlours import Parlour
from open_source import webtokens
from open_source import config
from open_source.core.resources import USER_RESET_PASSWORD_EMAIL_TEMPLATE


from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


logger = logging.getLogger(__name__)

conf = config.get_config()

public_cors = CORS(allow_all_origins=True)

def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


def authenticate_consultant_by_email(session, email, password):
    consultant = session.query(Consultant)\
        .filter(
            Consultant.email == email,
            Consultant.state == Consultant.STATE_ACTIVE
    ).one_or_none()

    return consultant, False if consultant is None else consultant.authenticate(password)


def authenticate_consultant_by_username(session, username, password):
    consultant = session.query(Consultant)\
        .filter(
            Consultant.username == username,
            Consultant.state == Consultant.STATE_ACTIVE
    ).one_or_none()

    return consultant, False if consultant is None else consultant.authenticate(password)


class ConsultantGetEndpoint:
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
                consultant = session.query(Consultant).filter(
                    Consultant.id == id,
                    Consultant.state == Consultant.STATE_ACTIVE
                ).first()
                if consultant is None:
                    raise falcon.HTTPNotFound(title="Consultant Not Found")

                resp.body = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Consultant with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant with ID {}.".format(id))


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

                consultants = session.query(Consultant).filter(
                    Consultant.state == Consultant.STATE_ACTIVE,
                    Consultant.parlour_id == parlour.id
                ).all()

                if consultants:
                    resp.body = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))


class ConsultantGetEndpoint:
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
                consultant = session.query(Consultant).filter(
                    Consultant.id == id,
                    Consultant.state == Consultant.STATE_ACTIVE
                ).first()

                if consultant is None:
                    raise falcon.HTTPNotFound(title="Consultant Not Found")

                resp.body = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Consultant with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant with ID {}.".format(id))


class ConsultantPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:

                if 'email' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing email field.")
                if 'first_name' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing first_name field.")
                if 'last_name' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing last_name field.")
                if 'username' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing email field.")
                if 'email' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing username field.")
                if 'branch' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing branch field.")

                parlour = session.query(Parlour).get(req["parlour_id"])
                if not parlour:
                    raise falcon.HTTPNotFound(title="404 Error", description="Parlour not found.")

                consultant_exists = session.query(Consultant).filter(
                    Consultant.email == req["email"],
                    Consultant.state == Consultant.STATE_ACTIVE).first()

                if consultant_exists:
                    raise falcon.HTTPBadRequest(title="Error", description="Email already exists. Email must be unique")

                consultant = Consultant(
                    first_name = req['first_name'],
                    last_name = req['last_name'],
                    email = req['email'],
                    branch = req['branch'],
                    number = req['number'],
                    username = req['username'],
                    parlour_id = req["parlour_id"],
                    state=Consultant.STATE_ACTIVE,
                )

                consultant.temp_password = consultant.generate_password()
                consultant.set_password(consultant.temp_password)

                consultant.save(session)
                consultant_dict = consultant.to_dict()
                resp.body = json.dumps(consultant_dict, default=str)
        except Exception as e:
            logger.exception(
                "Error, experienced error while creating Consultant.")
            raise e


class ConsultantPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTPBadRequest(title="Missing Field", description="Missing email field.")

                consultant = session.query(Consultant).filter(
                    Consultant.id == id).first()

                if not consultant:
                    raise falcon.HTTPNotFound(title="Consultant not found", description="Could not find consultant with given ID.")

                consultant.first_name = req['first_name']
                consultant.last_name = req['last_name']
                consultant.email = req['email']
                consultant.branch = req['branch']
                consultant.number = req['number']
                consultant.username = req['username']
                consultant.save(session)
                resp.body = json.dumps(consultant.to_dict(), default=str)
        except Exception as e:
            logger.exception(
                "Error, experienced error while creating Consultant.")
            raise e


class ConsultantChangePasswordEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:
                if 'password' not in req or req.get("password").strip() == '':
                    raise falcon.HTTPBadRequest(title="Missing Field", description="Missing password field.")

                if 'confirmPassword' not in req or req.get("confirmPassword").strip() == '':
                    raise falcon.HTTPBadRequest(title="Missing Field", description="Missing confirm password field.")

                if req.get("password") != req.get("confirmPassword"):
                    raise falcon.HTTPBadRequest(title="Error", description="Password and confirm password must be the same.")

                consultant = session.query(Consultant).filter(
                    Consultant.id == id).first()

                if not consultant:
                    raise falcon.HTTPNotFound(title="Consultant not found", description="Could not find consultant with given ID.")

                consultant.set_password(req.get("password"))
                consultant.save(session)
                resp.body = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Consultant.")
            # raise falcon.HTTPBadRequest(
            #     "Processing Failed. experienced error while creating Consultant.")


class ConsultantDeleteEndpoint:

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
                consultant = session.query(Consultant).filter(Consultant.id == id).first()

                if consultant is None:
                    raise falcon.HTTPNotFound(title="Not Found",  description="Consultant Not Found")
                if consultant.is_deleted:
                    falcon.HTTPNotFound(title="Not Found",  description="Consultant does not exist.")

                consultant.delete(session)
                resp.body = json.dumps(consultant.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete Consultant with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Consultant with ID {}.".format(id))


class ChangeUserPasswordEndpoint:

    def on_post(self, req, resp, id):
        with db.transaction() as session:
            # parlour = session.query(Parlour).filter(Parlour.id == id).first()
            consultant = session.query(Consultant).filter(
                Consultant.id == id,
                Consultant.state == Consultant.STATE_ACTIVE
            ).first()

            # parlour_id = '{}'.format(parlour.id)

            if consultant.id != id:
                # Currently logged in user should not be able to
                # change other user's passwords unless Super Admin
                raise falcon.HttpValidationError(
                    {'user': 'You may not set another user\'s password'})
            
            if consultant.password != consultant.set_password(req["current_password"]):
                raise falcon.HTTPBadRequest(title="Error", description="Current Password is incorrect")

            if not req.get("password") or not req.get("confirm_password"):
                raise falcon.HTTPBadRequest(title="Error", description="Missing field(s)")

            if req["password"] != req["confirm_password"]:
                raise falcon.HTTPBadRequest(title="Error", description="Password and confirmpassword must match")

            consultant.set_password(req['password'])
            session.commit()
            resp.body = json.dumps(consultant.to_dict())


class ConsultantGetAllPendingEndpoint:
    # cors = public_cors
    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                consultants = session.query(Consultant).filter(Consultant.state == Consultant.STATE_PENDING).all()

                if consultants:
                    resp.body = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))


class ConsultantGetAllArchivedEndpoint:
    # cors = public_cors
    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                consultants = session.query(Consultant).filter(Consultant.state == Consultant.STATE_ARCHIVED).all()

                if consultants:
                    resp.body = json.dumps([consultant.to_dict() for consultant in consultants], default=str)
                else:
                    resp.body = json.dumps([])

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Consultant for user with ID {}.".format(id))


class ConsultantAuthEndpoint:
    # cors = public_cors
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
                        title='Consultant400 Malformed Auth request',
                        description='Missing credential[password]'
                    )

                password = rest_dict.get('password')
                user, success = utils.authenticate(session, username, password)

                if success:
                    # write_audit_log(user, session)
                    text = webtokens.create_token_from_consultant(user)

                    resp.body = json.dumps(
                        {
                            'user': user.to_dict(),
                            "token": text,
                            "permission": "Consultant"
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
            raise e


class ConsultantSignupEndpoint:

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
            parlour = session.query(Parlour).filter(
                Parlour.id == rest_dict.get("parlour_id"),
                Parlour.state == Parlour.STATE_ACTIVE
            ).first()

            if not parlour:
                raise falcon.HTTPUnauthorized(title="Missing Parlour", description="Parlour does not exist")

            if not rest_dict.get('email'):
                raise falcon.HTTPBadRequest(title="Email", description="Email is a required field.")

            if not rest_dict.get('username'):
                raise falcon.HTTPBadRequest(title="Username", description="Username is a required field.")

            rest_dict['email'] = rest_dict['email'].lower().strip()

            email = rest_dict.get('email')

            user = Consultant()

            if not utils.is_username_unique(session, rest_dict.get("username")):
                errors['username'] = 'Username {} is already in use.'.format(
                    user.username)

            if not utils.is_valid_email_address(email):
                errors['email'] = 'Email must be a valid email address'

            if not utils.is_email_unique(session, email):
                errors['email'] = 'Email address {} is already in use.'.format(
                    email)

            if errors:
                raise falcon.HTTPBadRequest(errors)

            user.email = email
            user.username=rest_dict.get("username")
            user.first_name=rest_dict.get("first_name")
            user.last_name=rest_dict.get("last_name")
            user.state=Consultant.STATE_ACTIVE
            user.branch=rest_dict.get("branch")
            user.number=rest_dict.get("number")
            user.modified_at=datetime.now()
            user.created_at=datetime.now()
            user.parlour_id=rest_dict.get("parlour_id")

            passowrd = user.generate_password()
            user.temp_password = passowrd
            user.set_password(passowrd)

            user.save(session)

            user_dict = user.to_dict()

            resp.body = json.dumps({
                'id': user_dict['id'],
                'email': user_dict.get('email'),
            })


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
            
            rest_dict = json.load(req.bounded_stream)

            email = None

            user = None

            if 'email' in rest_dict:
                email = rest_dict.get('email')

            if not email:
                raise falcon.HTTPBadRequest(title='Error', description='An email address or username is required')

            # if email and not user_identifier:
            user = self.get_user_by_email(session, email)
            if not user:
                raise falcon.HTTPBadRequest(title='Error', description='Email address does not exist')
            #  DoNotReply@osource.co.za 
            # 7BHC9ko7T

            # session.add(user)
            # session.commit()

            import smtplib, ssl
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            port = 465  # For SSL
            smtp_server = "smtp.gmail.com"
            sender_email = "nkosananikani@gmail.com"  # Enter your address
            receiver_email = email  # Enter receiver address
            password = '3McsgoId1grf'

            message = MIMEMultipart("alternative")
            message["Subject"] = "multipart test"
            message["From"] = sender_email
            message["To"] = receiver_email

            # Create the plain-text and HTML version of your message
            # text = """\
            # Hi,
            # How are you?
            # Real Python has many great tutorials:
            # www.realpython.com"""
            # html = """\
            # <html>
            # <body>
            #     <p>Hi,<br>
            #     <a href="http://localhost:4200/reset-password?email={email}">Reset password</a> 
                
            #     </p>
            # </body>
            # </html>
            # """.format(email=email)

            args = {
                "user": user.pretty_name,
                "domain": conf.url,
                "email": email,
                "year": datetime.now().year
            }

            email_body = utils.render_template(
                USER_RESET_PASSWORD_EMAIL_TEMPLATE,
                args
            )

            subject = "Change of banking details"


            # Turn these into plain/html MIMEText objects
            # part1 = MIMEText(text, "plain")
            part2 = MIMEText(email_body, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            # message.attach(part1)
            message.attach(part2)
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())

            resp.body = json.dumps({'status': 'success'})

    def get_user_by_email(self, session, email):
        try:
            user =  session.query(Consultant)\
                .filter(Consultant.email == email, Consultant.state == Consultant.STATE_ACTIVE).one_or_none()
            if not user:
                user =  session.query(Parlour)\
                .filter(Parlour.email == email, Parlour.state == Parlour.STATE_ACTIVE).one_or_none()

        except MultipleResultsFound:
            return None

        return user
