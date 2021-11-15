import json
import logging

import falcon

logger = logging.getLogger(__name__)


def get_user(session, req):
    user = req.context.get('user')
    if not user:
        raise KeyError('Missing user from request context')
    # reattach the user to the session
    if user not in session:
        session.add(user)
    return user


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))
