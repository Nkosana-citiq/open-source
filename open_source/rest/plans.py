import falcon
import json
import logging

from open_source import db

from open_source.core.plans import Plan

logger = logging.getLogger(__name__)


class PlanGetEndpoint:

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                plan = session.query(Plan).filter(
                    Plan.plan_id == id,
                    Plan.state == Plan.STATE_ACTIVE
                ).first()
                if plan is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")

                resp.text = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Parlour with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Card with ID {}.".format(id))


class PlanGetAllEndpoint:

    def on_get(self, req, resp):
        try:
            with db.transaction() as session:
                plans = session.query(Plan).filter(Plan.state == Plan.STATE_ACTIVE).all()
                if plans:
                    resp.text = json.dumps([plan.to_dict() for plan in plans], default=str)
                resp.body = json.dumps([])
                
        except:
            logger.exception("Error, Failed to get Card for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Card for user with ID {}.".format(id))


class PlanPostEndpoint:

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                plan_exists = session.query(Plan).filter(
                    Plan.email == req["email"]).first()

                if not plan_exists:
                    plan = Plan(
                        plan=req["plan"],
                        cover = req["cover"],
                        premium = req["premium"],
                        member_age_restriction = req["member_age_restriction"],
                        member_minimum_age = req["member_minimum_age"],
                        member_maximum_age = req["member_maximum_age"],
                        beneficiaries = req["beneficiaries"],
                        consider_age = req["consider_age"],
                        minimum_age = req["minimum_age"],
                        maximum_age = req["maximum_age"],
                        has_benefits = req["has_benefits"],
                        benefits = req["benefits"],
                        state=Plan.STATE_ACTIVE,
                    )
                    plan.save(session)
                    resp.text = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class PlanPutEndpoint:

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                plan = session.query(Plan).filter(
                    Plan.plan_id == id).first()

                if not plan:
                    raise falcon.HTTPNotFound(title="Parlour not found", description="Could not find parlour with given ID.")
            
                plan.plan=req["plan"],
                plan.cover = req["cover"],
                plan.premium = req["premium"],
                plan.member_age_restriction = req["member_age_restriction"],
                plan.member_minimum_age = req["member_minimum_age"],
                plan.member_maximum_age = req["member_maximum_age"],
                plan.beneficiaries = req["beneficiaries"],
                plan.consider_age = req["consider_age"],
                plan.minimum_age = req["minimum_age"],
                plan.maximum_age = req["maximum_age"],
                plan.has_benefits = req["has_benefits"],
                plan.benefits = req["benefits"],
                plan.save(session)
                resp.text = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Parlour.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Parlour.")


class PlanDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:
                plan = session.query(Plan).filter(Plan.parlour_id == id).first()

                if plan is None:
                    raise falcon.HTTPNotFound(title="Parlour Not Found")
                if plan.is_deleted:
                    falcon.HTTPNotFound("Parlour does not exist.")

                plan.delete(session)
                resp.text = json.dumps({})
        except:
            logger.exception("Error, Failed to delete Parlour with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Parlour with ID {}.".format(id))
