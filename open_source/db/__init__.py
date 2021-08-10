from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from open_source.config import get_config

config = get_config()


def init(db_url, db_params, _is_prod):
    global engine, Session, is_prod
    engine = create_engine(db_url, **db_params)
    Session = sessionmaker(bind=engine)
    is_prod = _is_prod


def assert_initialized():
    global engine, Session
    assert None not in (engine, Session), 'Initialize db by calling init.'


def assert_not_prod():
    global is_prod
    assert not is_prod, 'Not allowed in PROD'


def create_table(cls, checkfirst=True):
    assert_initialized()
    cls.__table__.create(engine, checkfirst=checkfirst)


def create_tables(checkfirst=True):
    assert_initialized()
    Base.metadata.create_all(engine, checkfirst=checkfirst)


def drop_tables():
    assert_initialized()
    assert_not_prod()
    Base.metadata.drop_all(engine)


def recreate_tables():
    assert_initialized()
    drop_tables()
    create_tables()


@contextmanager
def transaction():
    global Session
    assert_initialized()
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def no_transaction():
    global Session
    assert_initialized()
    session = Session()
    try:
        yield session
    finally:
        session.close()


init(config.db['url'], config.db['params'], config.is_prod())