import falcon
import json

from datetime import datetime, time

from open_source import db
from open_source.core.consultants import Consultant
from open_source.core.notifications import Notification
from open_source.core.parlours import Parlour

class ParlourNotificationsPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):

        with db.transaction() as session:
            rest_dict = json.load(req.bounded_stream)

            if not rest_dict.get('recepients'):
                raise falcon.HTTPBadRequest(title="Error", description="Users are required.")

            if not rest_dict.get('days'):
                raise falcon.HTTPBadRequest(title="Error", description="Days of the week are required.")

            if not rest_dict.get('time'):
                raise falcon.HTTPBadRequest(title="Error", description="Time to send notification not set.")

            if not rest_dict.get('consultants'):
                raise falcon.HTTPBadRequest(title="Error", description="Select at least one conusltant or select the parlour.")

            parlour = session.query(Parlour).filter(
                Parlour.id == id,
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest("Parlour does not exist.")

            days = ', '.join(set(rest_dict.get('days')))
            recipients = ', '.join(set(rest_dict.get('recepients')))
            consultants = ', '.join(set(rest_dict.get('consultants')))

            if "all" in consultants:
                consultants = [con.id for con in session.query(Consultant).filter(Consultant.parlour_id == parlour.id, Consultant.state == Consultant.STATE_ACTIVE).all()]

            notify_times = rest_dict.get('time').split(":")
            notify_time = time(int(notify_times[0]), int(notify_times[1]))

            notification = Notification(
                recipients = recipients,
                week_days = days,
                scheduled_time = notify_time,
                parlour_id = parlour.id,
                consultants = consultants,
                state = Notification.STATE_ACTIVE,
                modified_at = datetime.now(),
                created_at = datetime.now()
            )

            notification.save(session)

            resp.body = json.dumps([], default=str)


class ParlourNotificationsSendEmailEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):

        with db.transaction() as session:
            rest_dict = json.load(req.bounded_stream)

            if not rest_dict.get('recepients'):
                raise falcon.HTTPBadRequest(title="Error", description="Users are required.")

            if not rest_dict.get('consultants'):
                raise falcon.HTTPBadRequest(title="Error", description="Select at least one conusltant or select the parlour.")

            parlour = session.query(Parlour).filter(
                Parlour.id == id,
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest("Parlour does not exist.")

            recipients = ', '.join(set(rest_dict.get('recepients')))
            consultants = ', '.join(set(rest_dict.get('consultants')))

            if "all" in consultants:
                consultants = [con.id for con in session.query(Consultant).filter(Consultant.parlour_id == parlour.id, Consultant.state == Consultant.STATE_ACTIVE).all()]

            notification = Notification(
                recipients = recipients,
                parlour_id = parlour.id,
                consultants = consultants,
                state = Notification.STATE_ACTIVE,
                modified_at = datetime.now(),
                created_at = datetime.now()
            )

            Notification.send_email(session, notification, parlour)
            resp.body = json.dumps({"status": "Success"}, default=str)
