import datetime
from open_source.core import main_members
import falcon
import json
import logging

from open_source import db

from open_source.core.audit import AuditLogClient
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from falcon_cors import CORS


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)

class PlanGetEndpoint:
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
                plan = session.query(Plan).filter(
                    Plan.id == id,
                    Plan.state == Plan.STATE_ACTIVE
                ).first()
                if plan is None:
                    raise falcon.HTTPNotFound(title="Plan Not Found")
                # AuditLogClient.save_log(
                #     session,

                # )
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
                    Plan.parlour_id == parlour.id
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
                    raise falcon.HTTPBadRequest(titile="Parlour not found", description="Parlour does not exist.")

                plan_exists = session.query(Plan).filter(
                    Plan.plan == req["plan"],
                    Plan.parlour_id == parlour.id,
                    Plan.state == Plan.STATE_ACTIVE
                ).first()

                if plan_exists:
                    raise falcon.HTTPBadRequest(titile="Name exists", description="You already have a plan with this name.")

                plan = Plan(
                    plan=req["plan"],
                    cover = req["cover"],
                    premium = req["premium"],
                    underwriter_premium = req["underwriter_premium"],
                    main_members = req["main_members"],
                    member_age_restriction = req["member_age_restriction"],
                    member_minimum_age = req["member_minimum_age"],
                    member_maximum_age = req["member_maximum_age"],
                    beneficiaries = req["dependants"],
                    consider_age = req["consider_age"],
                    dependant_minimum_age = req["dependant_minimum_age"],
                    dependant_maximum_age = req["dependant_maximum_age"],
                    extended_members = req["extended_members"],
                    extended_age_restriction = req["extended_age_restriction"],
                    extended_minimum_age = req["extended_minimum_age"],
                    extended_maximum_age = req["extended_maximum_age"],
                    additional_extended_maximum_age = req['additional_extended_maximum_age'],
                    additional_extended_minimum_age = req["additional_extended_minimum_age"],
                    additional_extended_consider_age = req["additional_extended_consider_age"],
                    additional_extended_members = req["additional_extended_members"],
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
            raise falcon.HTTPBadRequest(
                title="Error",
                description="Processing Failed. experienced error while creating Plan.")


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

                plan = session.query(Plan).filter(
                    Plan.id == id).first()

                if not plan:
                    raise falcon.HTTPNotFound(title="Plan not found", description="Could not find plan with given ID.")

                plan.plan=req["plan"]
                plan.cover = req["cover"]
                plan.premium = req["premium"]
                plan.underwriter_premium = req["underwriter_premium"]
                plan.main_members = req["main_members"]
                plan.member_age_restriction = req["member_age_restriction"]
                plan.member_minimum_age = req["member_minimum_age"]
                plan.member_maximum_age = req["member_maximum_age"]
                plan.additional_extended_maximum_age = req['additional_extended_maximum_age']
                plan.additional_extended_minimum_age = req["additional_extended_minimum_age"] 
                plan.additional_extended_consider_age = req["additional_extended_consider_age"]
                plan.additional_extended_members = req["additional_extended_members"]
                plan.extended_members = req["extended_members"]
                plan.extended_age_restriction = req["extended_age_restriction"]
                plan.extended_minimum_age = req["extended_minimum_age"]
                plan.extended_maximum_age = req["extended_maximum_age"]
                plan.beneficiaries = req["dependants"]
                plan.consider_age = req["consider_age"]
                plan.dependant_minimum_age = req["dependant_minimum_age"]
                plan.dependant_maximum_age = req["dependant_maximum_age"]
                plan.has_benefits = req["has_benefits"]
                plan.benefits = req["benefits"]
                plan.modified_at = datetime.datetime.now()
                plan.save(session)
                resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Plan.")
            raise falcon.HTTPBadRequest(title="", description="Processing Failed. experienced error while creating Plan.")


class PlanDeleteEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:

                plan = session.query(Plan).get(id)

                if plan is None:
                    raise falcon.HTTPNotFound(title="404 Not Found", description="Plan Not Found")

                if plan.is_deleted():
                    falcon.HTTPNotFound(title="404 Not Found", description="Plan does not exist.")

                plan.delete(session)
                resp.body = json.dumps(plan.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete Plan with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Plan with ID {}.".format(id))
