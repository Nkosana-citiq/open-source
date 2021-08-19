import falcon
import json
import logging

from open_source import db

from open_source.core.main_members import MainMember

logger = logging.getLogger(__name__)


class MainMemberGetEndpoint:

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                main_member = session.query(MainMember).filter(
                    MainMember.id == id,
                    MainMember.state == MainMember.STATE_ACTIVE
                ).first()
                if main_member is None:
                    raise falcon.HTTPNotFound(title="Main member Not Found")

                resp.text = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get main member with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Main Member with ID {}.".format(id))


class MainMemberGetAllEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                main_members = session.query(MainMember).filter(MainMember.state == MainMember.STATE_ACTIVE).all()
                if main_members:
                    resp.text = json.dumps([main_member.to_dict() for main_member in main_members], default=str)
                resp.body = json.dumps([])
                
        except:
            logger.exception("Error, Failed to get Main Members for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Main Members for user with ID {}.".format(id))


class MainMemberPostEndpoint:

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:

                main_member_exists = session.query(MainMember).filter(
                    MainMember.id_number == req["id_number"]).first()

                if not main_member_exists:
                    main_member = MainMember(
                        pid_number = req["id_number"],
                        date_of_birth =  req["date_of_birth"],
                        state = req["state"],
                        first_name = req["first_name"],
                        last_name = req["last_name"],
                        contact = req["contact"],
                        created_at = req["created_at"],
                        parlour_id = req["parlour_id"],
                        plan_id = req["plan_id"],
                        state=MainMember.STATE_ACTIVE,
                    )
                    main_member.save(session)
                    resp.text = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Main Member.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Main Member.")


class MainMemberPutEndpoint:

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                main_member = session.query(MainMember).filter(
                    MainMember.id == id).first()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Main Member not found", description="Could not find Main Member with given ID.")

                main_member.pid_number = req["id_number"],
                main_member.date_of_birth =  req["date_of_birth"],
                main_member.first_name = req["first_name"],
                main_member.last_name = req["last_name"],
                main_member.contact = req["contact"],
                main_member.created_at = req["created_at"],
                main_member.parlour_id = req["parlour_id"],
                main_member.plan_id = req["plan_id"],
                main_member.save(session)
                resp.text = json.dumps(main_member.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Main Member.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Main Member.")


class MainMemberDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                main_member = session.query(MainMember).filter(MainMember.id == id).first()

                if main_member is None:
                    raise falcon.HTTPNotFound(title="Main Member Not Found")
                if main_member.is_deleted:
                    falcon.HTTPNotFound("Main Member does not exist.")

                main_member.delete(session)
                resp.text = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Main Member with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Main Member with ID {}.".format(id))
