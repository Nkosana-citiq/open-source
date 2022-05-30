from datetime import datetime, timedelta
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from open_source import utils
from open_source import config, db
from open_source.core.applicants import Applicant
from open_source.core.payments import Payment
from open_source.core.invoices import Invoice
from open_source.core.parlours import Parlour, Notification
from open_source.core.consultants import Consultant
from open_source.core.resources import DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE

from sqlalchemy import func


conf = config.get_config()


def get_money_collected(session, consultant):
    applicants = session.query(Applicant).filter(Applicant.consultant_id == consultant.id, Applicant.state == Applicant.STATE_ACTIVE).all()
    applicant_ids = [applicant.id for applicant in applicants]

    yesterday = datetime.today() - timedelta(days=1)

    payments =  session.query(Payment).filter(Payment.applicant_id.in_(applicant_ids), func.date(Payment.date) == yesterday.date()).all()
    payment_ids = [payment.id for payment in payments]

    invoices =  session.query(Invoice).filter(Invoice.payment_id.in_(payment_ids), Invoice.state == Invoice.STATE_ACTIVE).all()

    return sum([invoice.amount for invoice in invoices])


def send_email(session, notice, parlour):
    port = 465  # For SSL
    smtp_server = "mail.osource.co.za"
    sender_email = conf.SENDER_EMAIL
    receiver_email = notice.recipients.split(',')  # Enter receiver address
    password = conf.SENDER_PASSWORD

    message = MIMEMultipart("alternative")
    message["Subject"] = "DAILY REPORT"
    message["From"] = sender_email
    message["To"] = receiver_email
    consultants = []
    sum = 0

    for email in notice.consultants.split(", "):
        consultant = session.query(Consultant).filter(Consultant.email == email, Consultant.state == Consultant.STATE_ACTIVE).first()
        amount = get_money_collected(session, consultant, parlour)

        entry = """
        <tr>
            <td>{} {}</td>
            <td>R{}</td>
        </tr>""".format(consultant.first_name, consultant.last_name, amount)
        consultants.append(entry)
        sum += amount

    html = {"html": """
        {}
        <tr>
            <td>------------------------------------------------------------------------------------------------------------------------------</td>
        </tr>
        <tr>
            <td>{}</td>
            <td>R{}</td>
        </tr>
        """.format(''.join(consultants), parlour.parlourname, sum)}
    
    email_body = utils.render_template(
        DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE,
        html
    )    

    # Turn these into plain/html MIMEText objects
    # part1 = MIMEText(text, "plain")
    part2 = MIMEText(email_body, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    # message.attach(part1)
    message.attach(part2)
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def get_parlour(session, notice):
    parlour = session.query(Parlour).get(notice.parlour_id)
    return parlour


def cli():
    with db.no_transaction() as session:
        print("================================ START ===============================")
        notifications = session.query(Notification).filter(Notification.state == Notification.STATE_ACTIVE).order_by(Notification.parlour_id).all()
        
        for notice in notifications:
            try:
                print(notice)
                print(notice.recipients)
                parlour = get_parlour(session, notice)
                if str(datetime.now().weekday()) in  notice.week_days.split(", "):
                    if datetime.now().time() > notice.scheduled_time:
                        print("============================================= SEND EMAIL ==================================================")
                        send_email(session, notice, parlour)
            except:
                continue
        print("================================ END ===============================")


if __name__ == "__main__":
    cli()
