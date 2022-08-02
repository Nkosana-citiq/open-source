import falcon
import json

from datetime import datetime, time

from open_source import db
from open_source.core.consultants import Consultant
from open_source.core.notifications import Notification
from open_source.core.parlours import Parlour
from falcon_cors import CORS


public_cors = CORS(allow_all_origins=True)


class NotificationGetEndpoint:
    cors = public_cors
    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_get(self, req, resp, id):
        with db.transaction() as session:
            notification = session.query(Notification).filter(
                Notification.parlour_id == id,
                Notification.state == Notification.STATE_ACTIVE
            ).first()

            if notification is None:
                resp.body = json.dumps({}, default=str)
            else:
                resp.body = json.dumps(notification.to_dict(), default=str)


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

            if not rest_dict.get('recipients'):
                raise falcon.HTTPBadRequest(title="Error", description="Email recipients are required.")

            if not rest_dict.get('days'):
                raise falcon.HTTPBadRequest(title="Error", description="Days of the week are required.")

            if not rest_dict.get('consultants'):
                raise falcon.HTTPBadRequest(title="Error", description="Select at least one conusltant or select the parlour.")

            parlour = session.query(Parlour).filter(
                Parlour.id == id,
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest("Parlour does not exist.")

            days = ', '.join(set(rest_dict.get('days')))
            recipients = ', '.join(set(rest_dict.get('recipients')))
            consultants = ', '.join(set(rest_dict.get('consultants')))

            # if "all" in consultants:
            #     cons = [con.id for con in session.query(Consultant).filter(Consultant.parlour_id == parlour.id, Consultant.state == Consultant.STATE_ACTIVE).all()]
            #     consultants = ', '.join(str(v) for v in set(cons))

            try:
                notification = session.query(Notification).filter(Notification.parlour_id == parlour.id, Notification.state == Notification.STATE_ACTIVE).order_by(Notification.id.desc()).first()
                if notification:
                    notification.recipients = recipients,
                    notification.week_days = days,
                    notification.consultants = consultants,
                    notification.modified_at = datetime.now()
                else:
                    notification = Notification(
                        recipients = recipients,
                        week_days = days,
                        parlour_id = parlour.id,
                        consultants = consultants,
                        state = Notification.STATE_ACTIVE,
                        modified_at = datetime.now(),
                        created_at = datetime.now()
                    )
            except:
                raise falcon.HTTPBadRequest(title="Error", description="Error creating notification instance.")

            notification.save(session)

            resp.body = json.dumps(notification.to_dict(), default=str)


class ParlourNotificationsPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):

        with db.transaction() as session:
            rest_dict = json.load(req.bounded_stream)

            if not rest_dict.get('recipients'):
                raise falcon.HTTPBadRequest(title="Error", description="Email recipients are required.")

            if not rest_dict.get('days'):
                raise falcon.HTTPBadRequest(title="Error", description="Days of the week are required.")

            if not rest_dict.get('consultants'):
                raise falcon.HTTPBadRequest(title="Error", description="Select at least one conusltant or select the parlour.")

            days = ', '.join(set(rest_dict.get('days')))
            recipients = ', '.join(set(rest_dict.get('recipients')))

            try:
                notification = session.query(Notification).get(id)
                consultants = ', '.join(set(rest_dict.get('consultants')))

                # if "all" in consultants:
                #     parlour = notification.parlour
                #     cons = [con.id for con in session.query(Consultant).filter(Consultant.parlour_id == parlour.id, Consultant.state == Consultant.STATE_ACTIVE).all()]
                #     consultants = ', '.join(str(v) for v in set(cons))

                notification.recipients = recipients,
                notification.week_days = days,
                notification.consultants = consultants,
                notification.modified_at = datetime.now()
                notification.save(session)

            except Exception as e:
                raise falcon.HTTPBadRequest(title="Error", description="Error Updating notification instance.")

            resp.body = json.dumps(notification.to_dict(), default=str)


class ParlourNotificationsDeleteEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_delete(self, req, resp, id):

        with db.transaction() as session:

            try: 
                notification = session.query(Notification).get(id)
                notification.modified_at = datetime.now()
                notification.delete(session)

            except:
                raise falcon.HTTPBadRequest(title="Error", description="Error deleting notification instance.")

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

            if not rest_dict.get('recipients'):
                raise falcon.HTTPBadRequest(title="Error", description="Users are required.")

            if not rest_dict.get('consultants'):
                raise falcon.HTTPBadRequest(title="Error", description="Select at least one conusltant or select the parlour.")

            parlour = session.query(Parlour).filter(
                Parlour.id == id,
                Parlour.state == Parlour.STATE_ACTIVE).first()

            if not parlour:
                raise falcon.HTTPBadRequest("Parlour does not exist.")

            recipients = ', '.join(set(rest_dict.get('recipients')))
            consultants = ', '.join(set(rest_dict.get('consultants')))

            # if "all" in consultants:
            #     cons = [con.id for con in session.query(Consultant).filter(Consultant.parlour_id == parlour.id, Consultant.state == Consultant.STATE_ACTIVE).all()]
            #     consultants = ', '.join(str(v) for v in set(cons))

            notification = Notification(
                recipients = recipients,
                parlour_id = parlour.id,
                consultants = consultants,
                state = Notification.STATE_ACTIVE,
                modified_at = datetime.now(),
                created_at = datetime.now()
            )

            notification.send_email(session, parlour)
            resp.body = json.dumps({"status": "Success"}, default=str)