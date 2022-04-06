from open_source.rest import parlours
import random
import datetime
import calendar
import re
import falcon
from jinja2 import Template
from open_source.core import parlours, consultants, admins

from typing import Any, Iterable, Dict

from collections import defaultdict as ddict


def digits_only(s: str) -> str:
    """ Removes all non digits from s. """
    return ''.join(c for c in s if c.isdigit()) if s else s


def validate_msisdn(msisdn):
    """ Removes all non digits from msisdn except for addition operator if msisdn """
    return re.sub('[^\d+]', '', msisdn) if msisdn else msisdn


def get_attr(obj: Any, attr: str):
    """
    Returns the attribute named attr for this obj.

    Obj may be a dictionary or a python object.
    """
    return obj[attr] if isinstance(obj, dict) else getattr(obj, attr)


def collect(attr: str, xs: Iterable) -> Dict[str, Iterable]:
    """
    Collects the objects or dicts in xs by key.

    Usage::

        boys = [
            {'age': 12, 'name': 'tom'},
            {'age': 12, 'name': 'dick'},
            {'age': 13, 'harry'}
        ]

        collect('age', boys)
        >> {
            12: [
                {'age': 12, 'name': 'tom'},
                {'age': 12, 'name': 'dick'},
            ],
            13: [
                {'age': 13, 'harry'}
            ]
        }

    """
    results = ddict(list)
    for x in xs:
        results[get_attr(x, attr)].append(x)
    return results


def flatten(some_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a flattened version of some_dict.

    Usage::

        print(flatten({"a": {"b": "1"}}))
        => {
            "a.b": 1
        }

    :param some_dict: A Dict[str, Any] to flatten
    :return: A Dict[str, Any]
    """
    def fn(val, key=None, aggr=None):
        aggr = {} if aggr is None else aggr
        if isinstance(val, dict):
            for k, v in val.items():
                new_key = '{}.{}'.format(key, k) if key else k
                fn(v, new_key, aggr)
        else:
            aggr[key] = val
        return aggr

    return fn(some_dict)


def diff(d1, d2):
    d1, d2 = d1 or {}, d2 or {}
    d1, d2 = flatten(d1), flatten(d2)
    keys = set(list(d1.keys()) + list(d2.keys()))
    return {k: [d1.get(k), d2.get(k)]
            for k in keys if d1.get(k) != d2.get(k)}


def empty_or_none(text):
    return None if text is None else text.strip()


def start_of_month(dt=None):
    dt = dt or datetime.datetime.now()
    return datetime.datetime(dt.year, dt.month, 1)


def end_of_month(dt=None):
    dt = dt or datetime.datetime.now()
    return datetime.datetime(dt.year, dt.month, calendar.mdays[dt.month], 23, 59, 59)


def start_of_last_month(dt=None):
    dt = dt or datetime.datetime.now()
    previous_month = dt.month - 1
    if previous_month == 0:
        previous_month = 12
        return datetime.datetime(dt.year - 1, previous_month, 1)
    return datetime.datetime(dt.year, previous_month, 1)


def end_of_last_month(dt=None):
    dt = dt or datetime.datetime.now()
    last_month = start_of_month(dt) - datetime.timedelta(days=1)
    return datetime.datetime(last_month.year, last_month.month, last_month.day, 23, 59, 59)


def one_month_ago(dt=None):
    dt = dt or datetime.datetime.now()
    end_of_last_month = start_of_month(dt) - datetime.timedelta(days=1)

    if end_of_last_month.day < dt.day:
        return datetime.datetime(end_of_last_month.year, end_of_last_month.month, end_of_last_month.day)

    return datetime.datetime(end_of_last_month.year, end_of_last_month.month, dt.day)


def date_from_string(string):
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def date_string_from_datetime(dt):
    try:
        return datetime.datetime.strftime(dt, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def validate_date(string):
    try:
        date_from_string(string)
    except ValueError as e:
        raise falcon.BadQueryParamsError(str(e))


def format_token_code(txt):
    s = ''
    for i, c in enumerate(txt):
        s += c
        if (i+1) % 4 == 0:
            s += ' '
    return s.strip()


def format_dictionary_key_for_filename(entity: dict, key: str) -> str:
    """
    :param entity: dictionary
    :param key: string
    :return: string

    Usage::
        entity['name'] = ' Entity Name '

        format_dictionary_key_for_pdf_filename(entity, 'name')
            => entity_name
    """
    try:
        return entity[key].lower().strip().replace(' ', '_')
    except KeyError as e:
        raise falcon.ApplicationError(str(e))


def random_text(sz):
    chars = [c for c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRXYZ']
    return ''.join([chars[random.randint(0, len(chars) - 1)] for _ in range(sz)])


def is_valid_password(pwd):
    if len(pwd) < 8:
        return False
    return any([str(c).isdigit() for c in pwd])


def is_valid_email_address(email):
    return re.match('[^@]+@[^@]+\\.[^@]+', email)


def has_at_least_one_letter(text):
    return re.match('.*[a-zA-Z].*', text)


def normalize_str(s):
    return ' '.join([w for w in s.strip().split() if w])


def replace_ampersand(text):
    if text is None:
        return text
    return text.replace("&", " and ").replace("  ", " ")


def camel_case_to_snake_case(s: str) -> str:
    if s is None:
        return
    components = re.split(r'([A-Z][a-z0-9]+)', s)
    return '_'.join([x.lower() for x in components if len(x)])


def snake_case_to_camel_case(s: str) -> str:
    if s is None:
        return
    components = s.split('_')
    return ''.join([x.title() for x in components])


def humanize_snake_case(s: str) -> str:
    if s is None:
        return None
    return ' '.join(x.title() for x in re.split(r'[,\._]', s.lower()))

def is_email_unique(session, email):
    parlour = parlours.Parlour.is_email_unique(session, email)
    consultant = consultants.Consultant.is_email_unique(session, email)
    admin = admins.Admin.is_email_unique(session, email)
    return all([parlour, consultant, admin])


def is_username_unique(session, email):
    parlour = parlours.Parlour.is_username_unique(session, email)
    consultant = consultants.Consultant.is_username_unique(session, email)
    admin = admins.Admin.is_username_unique(session, email)
    return all([parlour, consultant, admin])

def authenticate_user_by_email(cls, session, email, password):
    entity = session.query(cls)\
        .filter(
            cls.email == email,
            cls.state == cls.STATE_ACTIVE
    ).one_or_none()

    if entity:
        return entity, entity.authenticate(password)
    return entity, False


def authenticate_user_by_username(cls, session, username, password):
    entity = session.query(cls)\
        .filter(
            cls.username == username,
            cls.state == cls.STATE_ACTIVE
    ).one_or_none()

    if entity:
        return entity, entity.authenticate(password)
    return entity, False


def authenticate_parlour(session, username, password):
    user, success = authenticate_user_by_username(parlours.Parlour, session, username, password)
    if success:
        return user, success
    return authenticate_user_by_email(parlours.Parlour, session, username, password)


def authenticate_admin(session, username, password):
    user, success = authenticate_user_by_username(admins.Admin, session, username, password)
    if success:
        return user, success
    return authenticate_user_by_email(admins.Admin, session, username, password)


def authenticate_consultant(session, username, password):
    user, success = authenticate_user_by_username(consultants.Consultant, session, username, password)
    if success:
        return user, success
    return authenticate_user_by_email(consultants.Consultant, session, username, password)


def authenticate(session, username, password):

    user, success = authenticate_parlour(session, username, password)
    if success:
        return user, success
    user, success = authenticate_consultant(session, username, password)

    if success:
        return user, success
    return authenticate_admin(session, username, password)


def render_template(template: str, args: dict):
    return Template(template).render(args)

def localize_contact(contact=[]):
        if len(contact) == 10:
            return ''.join(['+27', contact[1:]])
        elif len(contact) < 10:
            return ''.join(['+27', contact])
        return contact
