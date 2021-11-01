import os


EMAIL_TEMPLATES_PATH = os.path.dirname(__file__)


def get_email_template(filename) -> str:
    return get_template(filename, EMAIL_TEMPLATES_PATH)


def get_template(filename, dir) -> str:
    path = os.path.join(dir, filename)
    with open(path, 'r') as file:
        text = file.read()
    return text


USER_RESET_PASSWORD_EMAIL_TEMPLATE = get_email_template(
    'reset_password.html')