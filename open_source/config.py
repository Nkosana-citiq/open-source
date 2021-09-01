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

    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')

    db = {
        'url': "mysql://osourcec:opensource@{}/osourcec_opensource".format(MYSQL_HOST),
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
    ...


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
