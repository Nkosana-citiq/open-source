
from datetime import datetime

from open_source import db

from open_source.core.parlours import Parlour
from open_source.core.notifications import Notification


def get_parlour(session, notice):
    parlour = session.query(Parlour).get(notice.parlour_id)
    return parlour


def cli():
    with db.no_transaction() as session:
        notifications = session.query(Notification).filter(Notification.state == Notification.STATE_ACTIVE).order_by(Notification.parlour_id).all()
        errors = []
        for notification in notifications:
            try:
                parlour = get_parlour(session, notification)
                if str(datetime.now().weekday()) in  notification.week_days.split(", "):
                    if not notification.last_run_date:
                        notification.send_email(session, parlour)
                        notification.modified_at = datetime.now()
                        notification.last_run_date = datetime.now()
                    elif datetime.now().time() > notification.scheduled_time and datetime.now().date() > notification.last_run_date.date():
                        notification.send_email(session, parlour)
                        notification.modified_at = datetime.now()
                        notification.last_run_date = datetime.now()
                notification.save(session)
            except Exception as e:
                errors.append({"notification_id": notification.id, "error": str(e)})
                continue


if __name__ == "__main__":
    cli()
