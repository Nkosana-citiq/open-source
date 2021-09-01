import jwt
import json
import logging
import base64

import falcon

from open_source import db, webtokens, config


conf = config.get_config()

logger = logging.getLogger(__name__)


def raise_failed_authorization(msg='Auth failed: Invalid Token'):
    raise falcon.HTTPUnauthorized('401 Failed Authorization', msg, {})


def raise_forbidden():
    raise falcon.HTTPForbidden('403 Forbidden', 'You do not have the required permissions.')


class AuthMiddleware(object):

    def process_resource(self, req, resp, resource, params):

        if resource.is_basic_secure():
            self.check_basic_auth(req)

        elif not resource.is_not_secure() and req.method.lower() != 'options':
            token_payload = self.authorize_token(req)
            req.context['token_payload'] = token_payload

    @staticmethod
    def authorize_token(req):
        payload = {}
        text = req.get_header('Authorization')
        if not text:
            raise_failed_authorization('Authorization header is missing')
        auth = text.strip().split()
        if not len(auth) == 2 or auth[0].lower() != 'bearer':
            raise_failed_authorization('Header should be[Authorization: Bearer <token> ]')
        try:
            payload = webtokens.decode_token(str(auth[1]))
            if 'user' not in payload:
                raise_failed_authorization()
            env = payload['user'].get('env')
            if not env == config.get_role_name():
                raise_failed_authorization()

        except (json.decoder.JSONDecodeError, jwt.exceptions.DecodeError):
            logger.exception('Failed Auth')
            raise_failed_authorization()
        return payload

    @staticmethod
    def check_basic_auth(req):
        text = req.get_header('Authorization')
        if not text:
            raise_failed_authorization('Authorization header is missing')

        auth = text.strip().split()
        if not len(auth) == 2 or auth[0].lower() != 'basic':
            raise_failed_authorization('Header should be[Authorization: Basic <token> ]')
        secret = base64.standard_b64encode(bytes(conf.basic_secret, 'ascii'))
        if str(secret, encoding='ascii') != str(auth[1]):
            raise_failed_authorization()


# class PermissionMiddleware(object):

#     def process_resource(self, req, resp, resource, params):
#         if not resource.is_basic_secure() and not resource.is_not_secure() and req.method.lower() != 'options':
#             from open_source.core.consultants import Consultant
#             from open_source.core.parlours import Parlour

#             token_payload = req.context.get('token_payload')
#             if not token_payload:
#                 raise falcon.HTTPInternalServerError('500 Internal Server Error',
#                                                      'Permission middleware require token_payload')

#             with db.no_transaction() as session:
#                 user = session.query(Consultant).get(token_payload['user']['id'])
#                 if not user or not user.is_active():
#                     user = session.query(Parlour).get(token_payload['user']['id'])
#                     if not user or not user.is_active():
#                         raise_failed_authorization('Unknown user.')
#                 # if not user.can_login():
#                 #     raise_failed_authorization('User not active for vendsystem.')
#                 req.context['user'] = user
#                 required_permission = resource.get_required_permission(req)
#                 if required_permission:
#                     permissions_names = [p.name for p in user.get_permissions()]
#                     if required_permission not in permissions_names:
#                         raise_forbidden()
#                 # detach user from the session
#                 session.expunge(user)


# class AsUserMiddleware(object):

#     def __init__(self, user_id):
#         self.user_id = user_id

#     def process_resource(self, req, resp, resource, params):
#         from admin_service.core.users import User

#         if not resource.is_not_secure():
#             with db.no_transaction() as session:
#                 user = session.query(User).get(self.user_id)
#                 session.expunge(user)
#                 req.context['user'] = user
