"""
Module for handling web token security using `JWT<https://jwt.io/>`_.
"""
import jwt

from open_source.config import get_config

# We need the config to get our secret
config = get_config()

# Chosen algorithm for web token encryption.
__algorithm__ = 'HS256'


def create_token_from_consultant(user) -> str:
    """Returns a token for the given user.

    :param user: A User.
    :return: A str that is the encoded token.
    """
    payload = {'user': user.to_webtoken_payload()}
    return encode_token(payload)


def create_token_from_parlour(user) -> str:
    """Returns a token for the given user.

    :param user: A User.
    :return: A str that is the encoded token.
    """
    payload = {'user': user.to_webtoken_payload()}
    return encode_token(payload)



def create_token_from_admin(user) -> str:
    """Returns a token for the given user.

    :param user: A User.
    :return: A str that is the encoded token.
    """
    payload = {'user': user.to_webtoken_payload()}
    return encode_token(payload)


def encode_token(payload: dict) -> str:
    """Returns a token from the given payload.

    :param payload: A dict to be encoded.
    :return: A str that is the token.
    """
    return jwt.encode(payload, config.jwt_secret, algorithm=__algorithm__)


def decode_token(token: str) -> dict:
    """Returns the payload from the given token.

    :param token: A str that is the token to be decoded.
    :return: A dict that is the tokens payload.
    """
    return jwt.decode(token, config.jwt_secret, algorithm=__algorithm__)
