from open_source import db, utils
from open_source.core.consultants import Consultant

def get_all_consultants(session, parlour_id):
    sql = "select id, temp_password, password from consultants where parlour_id=:parlour_id;"
    result =  session.execute(sql, {'parlour_id': parlour_id})
    return {row['id']: dict(row) for row in result}


def get_all_parlours(session):
    sql = "select * from parlours;"
    result =  session.execute(sql)
    return {row['id']: dict(row) for row in result}


def update_consultants(session, parlour):
    consultants = get_all_consultants(session, parlour['id'])
    for consultant in consultants.values():
        update_consultant = session.query(Consultant).get(consultant['id'])
        update_consultant.set_password(consultant['temp_password'])


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