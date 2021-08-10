import falcon
import json
import logging

from open_source import db

from open_source.core.parlours import Parlour

logger = logging.getLogger(__name__)


class ParlourGetEndpoint:

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(
                    Parlour.parlour_id == id,
                    Parlour.state == Parlour.STATE_ACTIVE
                ).first()
                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")

                resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Parlour with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Card with ID {}.".format(id))


class ParlourGetAllEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                parlours = session.query(Parlour).filter(Parlour.state == Parlour.STATE_ACTIVE).all()
                if parlours is None:
                    resp.body = json.dumps([])
                resp.text = json.dumps([parlour.to_dict() for parlour in parlours], default=str)
        except:
            logger.exception("Error, Failed to get Card for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Card for user with ID {}.".format(id))


class ParlourPostEndpoint:

    def on_post(self, req, resp):
        import datetime
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                parlour_exists = session.query(Parlour).filter(
                    Parlour.email == req["email"]).first()

                if not parlour_exists:
                    parlour = Parlour(
                        parlourname=req["parlour_name"],
                        personname=req["person_name"],
                        number=req["number"],
                        email=req["email"],
                        state=Parlour.STATE_ACTIVE,
                    )
                    parlour.save(session)
                    resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class ParlourPutEndpoint:

    def on_put(self, req, resp, id):
        import datetime
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                parlour = session.query(Parlour).filter(
                    Parlour.parlour_id == id).first()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
            
                parlour.parlourname=req["parlour_name"],
                parlour.personname=req["person_name"],
                parlour.number=req["number"],
                parlour.email=req["email"],
                parlour.state=Parlour.STATE_ACTIVE,
                parlour.save(session)
                resp.text = json.dumps(parlour.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class ParlourDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(Parlour.parlour_id == id).first()

                if parlour is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")
                if parlour.is_deleted:
                    falcon.HTTPNotFound("Parlour does not exist.")

                parlour.delete(session)
                resp.text = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Parlour with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Parlour with ID {}.".format(id))
