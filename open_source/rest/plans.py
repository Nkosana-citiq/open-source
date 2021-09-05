import falcon
import json
import logging

from open_source import db

from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from falcon_cors import CORS


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

class PlanGetEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                plan = session.query(Plan).filter(
                    Plan.id == id,
                    Plan.state == Plan.STATE_ACTIVE
                ).first()
                if plan is None:
                    raise falcon.HTTPNotFound(title="Plan Not Found")

                resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Plan with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Plan with ID {}.".format(id))


class PlanGetParlourAllEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(
                    Parlour.state == Parlour.STATE_ACTIVE,
                    Parlour.id == id).one_or_none()
                if not parlour:
                    raise falcon.HTTPBadRequest()

                plans = session.query(Plan).filter(
                    Plan.state == Plan.STATE_ACTIVE,
                    # Plan.parlour_id == parlour.id
                ).all()

                if not plans:
                    raise falcon.HTTPBadRequest()
                resp.body = json.dumps([plan.to_dict() for plan in plans], default=str)

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Plan for user with ID {}.".format(id))


class PlanPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                parlour = session.query(Parlour).filter(
                    Parlour.id == req["parlour_id"],
                    Parlour.state == Parlour.STATE_ACTIVE).first()

                if not parlour:
                    raise falcon.HTTP_BAD_REQUEST("Parlour does not exist.")

                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                plan_exists = session.query(Plan).filter(
                    Plan.plan == req["plan"],
                    Plan.state == Plan.STATE_ACTIVE).first()

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
                        state = Plan.STATE_ACTIVE,
                        parlour = parlour
                    )
                    plan.save(session)
                    resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Plan.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Plan.")


class PlanPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        req = json.loads(req.stream.read().decode('utf-8'))
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTP_BAD_REQUEST("Missing email field.")

                plan = session.query(Plan).filter(
                    Plan.id == id).first()

                if not plan:
                    raise falcon.HTTPNotFound(title="Plan not found", description="Could not find plan with given ID.")
            
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
                resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Plan.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Plan.")


class PlanDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:

                plan = session.query(Plan).filter(Plan.id == id).first()

                if plan is None:
                    raise falcon.HTTPNotFound(title="Plan Not Found")

                if plan.is_deleted():
                    falcon.HTTPNotFound("Plan does not exist.")

                plan.delete(session)
                resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete Plan with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Plan with ID {}.".format(id))
