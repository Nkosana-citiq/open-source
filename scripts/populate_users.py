
from re import A
from time import perf_counter
from open_source import db
from open_source.core import main_members
from open_source.core import applicants

from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from open_source.core.main_members import MainMember
from open_source.core.consultants import Consultant
from open_source.core.roles import Role
from open_source.core.users import User
from scripts import personal_docs


def get_parlour(session, notice):
    consultant = session.query(Parlour).get(notice.parlour_id)
    return consultant


def cli():
    with db.transaction() as session:
        consultants = session.query(Consultant).all()
        for consultant in consultants:
            try:
                result = session.execute(f"""
                    Insert into users(first_name, last_name, parlour_id, email, username, password, temp_password, branch, number, state, role_id, modified_at, created_at) 
                    values({consultant.first_name}, {consultant.last_name}, {consultant.parlour_id}, {consultant.email}, {consultant.username}, {consultant.password}, 
                    {consultant.temp_password}, {consultant.branch}, {consultant.number}, {consultant.state}, 3, {consultant.modified_at}, {consultant.created_at})
                """)
            except:
                ...
        # return result.rowcount

if __name__ == "__main__":
    print("Starting")
    cli()
