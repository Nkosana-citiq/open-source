from datetime import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from open_source import utils
from open_source import config
from open_source.core.applicants import Applicant
from open_source.core.extended_members import ExtendedMember
from open_source.core.main_members import MainMember
from open_source.core.resources import DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE

conf = config.get_config()

port = 465  # For SSL
smtp_server = "mail.osource.co.za"
sender_email = conf.SENDER_EMAIL
receiver_email = "nkosananikani@gmail.com"  # Enter receiver address
password = conf.SENDER_PASSWORD

message = MIMEMultipart("alternative")
message["Subject"] = "multipart test"
message["From"] = sender_email
message["To"] = receiver_email

html = {"html": """
    <tr>
        <td>Max Nongxa</td>
        <td>R5000</td>
    </tr>
    <tr>
        <td>Nkosana Nikani</td>
        <td>R4000</td>
    </tr>
    <tr>
        <td>Tumelo mabangula</td>
        <td>R6000</td>
    </tr>
    <tr>
        <td>-----------------------------------------------------------------------------------------------------------------------------------------</td>
    </tr>
    <tr>
        <td>Mqwathi Funerals</td>
        <td>R15000</td>
    </tr>
    """}

args = {
    "domain": conf.RESET_PASSWORD_URL,
    "email": "nkosananikani@gmail.com",
    "year": datetime.now().year
}

email_body = utils.render_template(
    DAILY_FINANCIAL_REPORT_PER_CONSULTANT_EMAIL_TEMPLATE,
    html
)

subject = "Change of banking details"


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
