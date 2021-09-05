from datetime import datetime
import falcon
import json
import logging

from open_source import db

from open_source.core.applicants import Applicant
from open_source.core.parlours import Parlour
from open_source.core.plans import Plan
from open_source.core.payments import Payment
from falcon_cors import CORS


logger = logging.getLogger(__name__)
public_cors = CORS(allow_all_origins=True)


def get_json_body(req):
    body = req.stream.read()

    if not body:
        raise falcon.HTTPBadRequest(title='400 Bad Request', description='Body is empty or malformed.')

    return json.loads(str(body, 'utf-8'))


class PaymentGetEndpoint:

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
                payment = session.query(Payment).filter(
                    Payment.payment_id == id,
                    Payment.state == Payment.STATE_ACTIVE
                ).first()
                if payment is None:
                    raise falcon.HTTPNotFound(title="Payment Not Found")

                resp.body = json.dumps(payment.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to get Payment with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Payment with ID {}.".format(id))


class PaymentsGetAllEndpoint:
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
                applicant = session.query(Applicant).filter(
                    Applicant.state == Applicant.STATE_ACTIVE,
                    Applicant.id == id
                ).one_or_none()

                if not applicant:
                    raise falcon.HTTPBadRequest()

                payments = session.query(Payment).filter(
                    Payment.state == Payment.STATE_ACTIVE,
                    Payment.applicant_id == applicant.id
                ).all()
                print(payments)
                if not payments:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([payment.to_dict() for payment in payments], default=str)

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Payment for user with ID {}.".format(id))


class PaymentPostEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp):
        try:
            with db.transaction() as session:
                rest_dict = get_json_body(req)
                parlour = session.query(Parlour).filter(
                    Parlour.id == rest_dict.get("parlour_id"),
                    Parlour.state == Parlour.STATE_ACTIVE
                ).one_or_none()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Not Found", description="Parlour does not exist.")

                plan = session.query(Plan).filter(
                    Plan.parlour_id == parlour.id,
                    Plan.id == rest_dict.get("plan_id"),
                    Plan.state == Plan.STATE_ACTIVE
                ).one_or_none()

                if not plan:
                    raise falcon.HTTPNotFound(title="Not Found", description="Plan does not exist.")

                applicant = session.query(Applicant).filter(
                    Applicant.parlour_id == parlour.id,
                    Applicant.id == rest_dict.get("applicant_id"),
                    Applicant.state == Applicant.STATE_ACTIVE
                ).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="Not Found", description="Applicant does not exist.")

                payment = Payment(
                    applicant=applicant,
                    parlour=parlour,
                    plan=plan,
                    date=datetime.now()
                )

                payment.save(session)
                resp.body = json.dumps(payment.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Payment.")
            raise falcon.HTTPBadRequest(
                "Processing Failed. experienced error while creating Payment.")


class PaymentPutEndpoint:

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

                payment = session.query(Payment).filter(
                    Payment.payment_id == id).first()

                if not payment:
                    raise falcon.HTTPNotFound(title="Payment not found", description="Could not find payment with given ID.")
            
                payment.payment=req["payment"],
                payment.cover = req["cover"],
                payment.premium = req["premium"],
                payment.member_age_restriction = req["member_age_restriction"],
                payment.member_minimum_age = req["member_minimum_age"],
                payment.member_maximum_age = req["member_maximum_age"],
                payment.beneficiaries = req["beneficiaries"],
                payment.consider_age = req["consider_age"],
                payment.minimum_age = req["minimum_age"],
                payment.maximum_age = req["maximum_age"],
                payment.has_benefits = req["has_benefits"],
                payment.benefits = req["benefits"],
                payment.save(session)
                resp.body = json.dumps(payment.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Payment.")
            raise falcon.HTTP_BAD_REQUEST(
                "Processing Failed. experienced error while creating Payment.")


class PaymentDeleteEndpoint:

    def on_delete(self, req, resp, id):
        try:
            with db.transaction() as session:

                payment = session.query(Payment).filter(Payment.payment_id == id).first()

                if payment is None:
                    raise falcon.HTTPNotFound(title="Payment Not Found")

                if payment.is_deleted():
                    falcon.HTTPNotFound("Payment does not exist.")

                payment.delete(session)
                resp.body = json.dumps(payment.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete Payment with ID {}.".format(id))
            raise falcon.HTTP_BAD_REQUEST("Failed to delete Payment with ID {}.".format(id))
