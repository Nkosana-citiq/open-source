
from open_source import db

from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from open_source.core.consultants import Consultant


def add_parlours(session):
    parlours = session.query(Parlour).all()

    for parlour in parlours:
        try:
            names = parlour.personname.split(" ")
            f_name = names[0]
            l_name = names [1] if len(names) > 1 else ""
            result = session.execute(f"""
                Insert into users(first_name, last_name, parlour_id, email, username, password, number, state, role_id, modified_at, created_at) 
                values({f_name}, {l_name}, {parlour.id}, {parlour.email}, {parlour.username}, {parlour.password}, 
                {parlour.number}, {parlour.state}, 2, {parlour.modified_at}, {parlour.created_at})
            """)
        except:
            ...


def add_consultants(session):
    consultants = session.query(Consultant).all()

    for consultant in consultants:
        try:
            session.execute(f"""
                Insert into users(first_name, last_name, parlour_id, email, username, password, temp_password, branch, number, state, role_id, modified_at, created_at) 
                values({consultant.first_name}, {consultant.last_name}, {consultant.parlour_id}, {consultant.email}, {consultant.username}, {consultant.password}, 
                {consultant.temp_password}, {consultant.branch}, {consultant.number}, {consultant.state}, 3, {consultant.modified_at}, {consultant.created_at})
            """)
        except:
            ...


def cli():
    with db.transaction() as session:
        add_parlours(session)
        add_consultants(session)
        # return result.rowcount


if __name__ == "__main__":
    cli()
