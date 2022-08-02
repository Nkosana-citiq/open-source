"""
Module for configurations. There are configurations per Role (Eg. DEV, TEST..).
Each Role must have its own configuration class that inherits from BaseConfig.
At run time you can set the configuration that gets used by setting the **ROLE** environment variable.
Usage::
    from comms_service.config import get_config
    conf = get_config()
    db_params = conf.db['params']
"""
import os


__role__ = os.environ.get('ROLE', 'LOCAL')


class BaseConfig(object):

    password_salt = 'DYhG93b0qyddddJfIxfs2guVoUubWwvniR2G0FgaC9mi'

    jwt_secret = 'db3b6cefdb2789e0'

    basic_secret = 'uGmZQhbCbp76ceJGG3h'

    SMS_AUTH_TOKEN = os.environ.get('SMS_AUTH_TOKEN', "Basic QzQzMzdGOERCODRDNEZGNEI5QzNCQzBGOThEM0I4M0UtMDEtOTpkS1l1cTdRb3VibllRTTlXVGtNRGNUTWlBWTJ2cQ==")
    SMS_FROM_NUMBER = os.environ.get('SMS_FROM_NUMBER', '+27796579128')

    RESET_PASSWORD_URL = os.environ.get('RESET_PASSWORD_URL', 'http://localhost:5100')

    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'DoNotReply@osource.co.za')
    SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'BbJoQ~@4*$i)')

    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'osource')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', 3306)
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'admin')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'osource_opensource')

    db = {
        'url': "mysql://{user}:{passwd}@{host}:{port}/{db}".format(user=MYSQL_USER, passwd=MYSQL_PASSWORD, host=MYSQL_HOST, port=MYSQL_PORT, db=MYSQL_DATABASE),
        'params': {'echo': False, 'pool_recycle': 3600, 'pool_size': 2}
    }

    @classmethod
    def is_test(cls):
        return False

    @classmethod
    def is_preprod(cls):
        return False

    @classmethod
    def is_prod(cls):
        return False

    @classmethod
    def is_dev(cls):
        return False

    @classmethod
    def is_local(cls):
        return False


class DevConfig(BaseConfig):

    @classmethod
    def is_dev(cls):
        return True


class TestConfig(BaseConfig):

    @classmethod
    def is_test(cls):
        return True


class LocalConfig(BaseConfig):

    @classmethod
    def is_local(cls):
        return True


class PreprodConfig(BaseConfig):
    ...

class ProdConfig(BaseConfig):

    url = 'http://localhost:4200'

    db = {
        'url': "mysql://eqa4wgn58w5q1nf4:r6rymog3csc13962@ulsq0qqx999wqz84.chr7pe7iynqr.eu-west-1.rds.amazonaws.com:3306/isupkx8fnsnozbtg",
        'params': {'echo': False, 'pool_recycle': 3600, 'pool_size': 2}
    }


    @classmethod
    def is_prod(cls):
        return True


__configs__ = {
    'LOCAL': LocalConfig,
    'DEV': DevConfig,
    'TEST': TestConfig,
    'PREPROD': PreprodConfig,
    'PROD': ProdConfig
}


def get_config(role=__role__):
    return __configs__.get(role)
