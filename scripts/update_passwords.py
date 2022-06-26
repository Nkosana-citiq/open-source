from .open_source import db, utils
from .open_source.core.users import User

def get_all_users_with_role_consultants(session, parlour_id):
    sql = "select id, temp_password, password from users where parlour_id=:parlour_id and role_id=3;"
    result =  session.execute(sql, {'parlour_id': parlour_id})
    return {row['id']: dict(row) for row in result}


def get_all_parlours(session):
    sql = "select * from parlours;"
    result =  session.execute(sql)
    return {row['id']: dict(row) for row in result}


def update_consultants(session, parlour):
    users = get_all_users_with_role_consultants(session, parlour['id'])
    for user in users.values():
        update_consultant = session.query(User).get(user['id'])
        print("set new password")
        update_consultant.set_password(user['temp_password'])


def update_consultant_passwords():
    with db.transaction() as session:
        parlours_by_id = get_all_parlours(session)
        for parlour in parlours_by_id.values():
            update_consultants(session, parlour)


def cli():
    update_consultant_passwords()
    # get_all_consultants()


if __name__ == '__main__':
    cli()