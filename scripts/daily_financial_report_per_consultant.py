
from datetime import datetime

from open_source import db

from open_source.core.parlours import Parlour, Notification


def get_parlour(session, notice):
    parlour = session.query(Parlour).get(notice.parlour_id)
    return parlour


def cli():
    with db.no_transaction() as session:
        notifications = session.query(Notification).filter(Notification.state == Notification.STATE_ACTIVE).order_by(Notification.parlour_id).all()

        for notice in notifications:
            try:
                parlour = get_parlour(session, notice)
                if str(datetime.now().weekday()) in  notice.week_days.split(", "):
                    if datetime.now().time() > notice.scheduled_time:
                        Notification.send_email(session, notice, parlour)
            except:
                continue


if __name__ == "__main__":
    cli()
