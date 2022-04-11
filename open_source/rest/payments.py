from datetime import datetime, timedelta
from borb.pdf.canvas.layout.text.heading import Heading
import falcon
import json
import logging
import random
import os
import uuid

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from open_source import db

from open_source.core.applicants import Applicant
from open_source.core.main_members import MainMember
from open_source.core.invoices import Invoice
from open_source.core.parlours import Parlour
from open_source.core.consultants import Consultant
from open_source.core.plans import Plan
from open_source.core.payments import Payment
from falcon_cors import CORS

from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable as Table
from borb.pdf.canvas.layout.text.paragraph import Paragraph

from borb.pdf.document import Document
from borb.pdf.page.page import Page
from borb.pdf.page.page_size import PageSize
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.layout_element import Alignment
from decimal import Decimal
from borb.pdf.pdf import PDF
import PyPDF2
import pandas as pd

from open_source.config import get_config


conf = get_config()


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


class PaymentGetLastEndpoint:

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

                applicant = session.query(Applicant).filter(Applicant.id == id).first()

                payment = session.query(Payment).filter(
                    Payment.applicant_id == applicant.id,
                    Payment.state == Payment.STATE_ACTIVE
                ).order_by(Payment.id.desc()).first()

                if payment is None:
                    resp.body = json.dumps([])
                else:
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

                if not payments:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([payment.to_dict() for payment in payments], default=str)

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Payment for user with ID {}.".format(id))


class PaymentPostEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_post(self, req, resp, id):
        try:
            with db.transaction() as session:
                rest_dict = json.load(req.bounded_stream)

                parlour = session.query(Parlour).filter(
                    Parlour.id == id,
                    Parlour.state == Parlour.STATE_ACTIVE
                ).one_or_none()

                if not parlour:
                    raise falcon.HTTPNotFound(title="Not Found", description="Parlour does not exist.")

                applicant_id = rest_dict.get("applicant_id")

                applicant = session.query(Applicant).filter(
                    Applicant.id == applicant_id,
                ).one_or_none()

                if not applicant:
                    raise falcon.HTTPNotFound(title="Not Found", description="Applicant does not exist.")

                main_member = session.query(MainMember).filter(
                    MainMember.applicant_id == applicant.id,
                ).one_or_none()

                if not main_member:
                    raise falcon.HTTPNotFound(title="Not Found", description="Main member does not exist.")

                plan = session.query(Plan).filter(
                    Plan.id == applicant.plan_id,
                    Plan.state == Plan.STATE_ACTIVE
                ).one_or_none()

                if not plan:
                    raise falcon.HTTPNotFound(title="Not Found", description="Plan does not exist.")

                start_date = datetime.strptime(rest_dict.get("date"), "%d/%m/%Y")
                end_date = datetime.strptime(rest_dict.get("end_date"), "%d/%m/%Y")

                if end_date < start_date: 
                    falcon.HTTPBadRequest(title="Error", description='End date cannot be earlier than start date')

                from dateutil.rrule import rrule, MONTHLY

                dates = [dt for dt in rrule(MONTHLY, dtstart=start_date.replace(day=1), until=end_date.replace(day=1))]

                amount = plan.premium * len(dates)
                payment = Payment(
                    applicant=applicant,
                    parlour=parlour,
                    plan=plan,
                    state=Payment.STATE_ACTIVE,
                    date=end_date,
                    payment_type=rest_dict.get("payment_type")
                )

                payment.save(session)
                Payment.update_payment_status(session, applicant)
                user = rest_dict.get("user")
                invoice = print_invoice(session, payment, applicant, user, amount, dates)

                resp.body = json.dumps(invoice.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Payment.")
            raise falcon.HTTPBadRequest(title="error",
            description="Processing Failed. experienced error while creating Payment.")


class RecieptGetEndpoint:

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

                invoice = session.query(Invoice).filter(
                    Invoice.id == id,
                    Invoice.state == Invoice.STATE_ACTIVE
                ).first()
                if not invoice:
                    raise falcon.HTTPNotFound(title="Error", description="Invoice not found")

                with open(invoice.document, 'rb') as f:
                    resp.downloadable_as = invoice.document
                    resp.content_type = 'application/pdf'
                    resp.stream = [f.read()]
                    resp.status = falcon.HTTP_200

                # resp.body = json.dumps(invoice.document, default=str)
        except:
            logger.exception("Error, Failed to get Payment with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed to get Invoice with ID {}.".format(id))


class PaymentPutEndpoint:

    def __init__(self, secure=False, basic_secure=False):
        self.secure = secure
        self.basic_secure = basic_secure

    def is_basic_secure(self):
        return self.basic_secure

    def is_not_secure(self):
        return not self.secure

    def on_put(self, req, resp, id):
        req = json.load(req.bounded_stream)
        try:
            with db.transaction() as session:
                if 'email' not in req:
                    raise falcon.HTTPBadRequest(title="Error", description="Missing email field.")

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
                user = req.get("user")

                resp.body = json.dumps(payment.to_dict(), default=str)
        except:
            logger.exception(
                "Error, experienced error while creating Payment.")
            raise falcon.HTTPBadRequest(title="Error",
            description="Processing Failed. experienced error while creating Payment.")


def print_invoice(session, payment, applicant, user, amount, dates):

    main_member = session.query(MainMember).filter(MainMember.applicant_id == applicant.id).first()
    last_invoice = session.query(Invoice).filter(Invoice.parlour_id == applicant.parlour.id).order_by(Invoice.id.desc()).first()
    invoice_number = str(int(last_invoice.number) + 1) if last_invoice else "1" 

    if main_member:
        if user.get("first_name"):
            assisted_by = '{}. {}'.format(user.get("first_name")[:1], user.get("last_name"))
        else:
            names = user.get("person_name").split() if user.get("person_name") else []
            last_name = names.pop()
            assisted_by = '{}. {}'.format('. '.join([n[:1] for n in names]), last_name)
        customer = '{}. {}'.format(main_member.first_name[:1], main_member.last_name) if main_member.first_name else None

        invoice = Invoice(
            state = Invoice.STATE_ACTIVE,
            created =  datetime.now(),
            payment_date = dates[-1],
            payment_id = payment.id,
            number = invoice_number,
            amount = amount,
            email = applicant.parlour.email,
            premium = applicant.plan.premium,
            parlour = applicant.parlour,
            address = applicant.parlour.address,
            branch = user.get("branch", ''),
            contact = applicant.parlour.number,
            policy_number = applicant.policy_num,
            id_number = main_member.id_number,
            customer = customer,
            assisted_by = assisted_by,
            number_of_months = str(len(dates)),
            months_paid = ", ".join([d.strftime("%b") for d in dates]),
            payment_type=payment.payment_type
        )

    # Create document
    pdf = Document()

    # Add page
    page = Page()
    pdf.append_page(page)
    page_layout = SingleColumnLayout(page, Decimal(0), Decimal(0))

    page_layout.vertical_margin = page.get_page_info().get_height() * Decimal(0.02)
    page_layout.add(Heading("       {}".format(invoice.parlour.parlourname), font="Helvetica-Bold", font_size=Decimal(13)))
    # Invoice information table
    page_layout.add(_build_invoice_information(invoice))

    # Empty paragraph for spacing
    page_layout.add(Paragraph(" "))

    os.chdir('./assets/uploads/receipts')
    filename = "{uuid}.{ext}".format(uuid=uuid.uuid4(), ext='pdf')
    path = '/'.join([os.getcwd(), filename])
    os.chdir('../../..')

    with open(path, "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)

    pdf = PyPDF2.PdfFileReader(path)
    page0 = pdf.getPage(0)
    page0.scaleTo(360, 480)  # float representing scale factor - this happens in-place
    writer = PyPDF2.PdfFileWriter()  # create a writer to save the updated results
    writer.addPage(page0)

    with open(path, "wb+") as file:
        writer.write(file)

    invoice.document = path
    invoice.save(session)
    invoice.path = "invoices/{}".format(invoice.id)
    session.commit()
    return invoice


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
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete Payment with ID {}.".format(id))


def _build_invoice_information(invoice):

    table_001 = Table(number_of_rows=33, number_of_columns=2, column_widths= [Decimal(2), Decimal(6)], horizontal_alignment=Alignment.LEFT)

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    paragraph = Paragraph("Date: ", font="Helvetica", font_size=Decimal(13))
    table_001.add(paragraph)
    now = datetime.now()
    table_001.add(Paragraph("%d/%d/%d" % (now.day, now.month, now.year), font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT,))


    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))


    address = invoice.address if invoice.address else " "
    table_001.add(Paragraph("Address: ", font="Helvetica", font_size=Decimal(13)))
    address = '{}\n{}'.format(address[:23], address[23:]) if len(address) > 23 else address
    table_001.add(Paragraph(address, respect_newlines_in_text=True, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))


    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Contact: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph(invoice.contact, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Email: ", font="Helvetica", font_size=Decimal(13)))
    email = invoice.email if invoice.email else " "
    email = '{}\n{}'.format(email[:23], email[23:]) if len(email) > 23 else email
    table_001.add(Paragraph('{}\n'.format(email), respect_newlines_in_text=True, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("---------------------------------------------------------------"))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Customer Details ", font="Helvetica-Bold", font_size=Decimal(13)))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Invoice: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph("#{}".format(invoice.number), font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Policy Number: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph("{}".format(invoice.policy_number), font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Premium: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph("R {}".format(invoice.premium), font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Initial and Surname: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph(invoice.customer, font="Helvetica", font_size=Decimal(16), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("ID Number: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph(invoice.id_number, font="Helvetica", font_size=Decimal(14), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Amount Paid: ", font="Helvetica", font_size=Decimal(13)))
    amount = str(invoice.amount) if invoice.amount else " "
    table_001.add(Paragraph("R {}".format(amount), font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Month Paid: ", font="Helvetica", font_size=Decimal(13)))
    months = invoice.number_of_months if invoice.number_of_months else " "
    table_001.add(Paragraph(months, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Months Paid For: ", font="Helvetica", font_size=Decimal(13)))
    months_paid = invoice.months_paid if invoice.months_paid else " "
    table_001.add(Paragraph(months_paid, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Type of Payment: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph(invoice.payment_type, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("Captured by: ", font="Helvetica", font_size=Decimal(13)))
    table_001.add(Paragraph(invoice.assisted_by, font="Helvetica", font_size=Decimal(13), horizontal_alignment=Alignment.LEFT))

    table_001.set_padding_on_all_cells(Decimal(2), Decimal(1), Decimal(2), Decimal(1))
    table_001.no_borders()
    return table_001


class InvoicesGetAllEndpoint:
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
                try:
                    applicant = session.query(Applicant).filter(
                        Applicant.id == id
                    ).one()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="More than one applicant with this ID.")
                except NoResultFound:
                    raise falcon.HTTPBadRequest(title="Error", description="No applicant fount with this ID.")

                payments = session.query(Payment).filter(
                    Payment.state == Payment.STATE_ACTIVE,
                    Payment.applicant_id == applicant.id
                ).all()

                invoices = None
                if payments:
                    invoices = session.query(Invoice).filter(
                        Invoice.state == Invoice.STATE_ACTIVE,
                        Invoice.payment_id.in_([p.id for p in payments])
                    ).all()

                if not invoices:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([invoice.to_dict() for invoice in invoices], default=str)

        except:
            logger.exception("Error, Failed to get Invoices for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed while getting invoices.")


class InvoicesGetEndpoint:
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
                try:
                    invoices = session.query(Invoice).filter(
                        Invoice.state == Invoice.STATE_ACTIVE,
                        Invoice.id == id
                    ).one()
                except MultipleResultsFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Found more than one invoice with this ID")
                except NoResultFound:
                    raise falcon.HTTPBadRequest(title="Error", description="Found more than one invoice with this ID")
                if not invoices:
                    resp.body = json.dumps([])
                else:
                    resp.body = json.dumps([invoice.to_dict() for invoice in invoices], default=str)

        except:
            logger.exception("Error, Failed to get Parlour for user with ID {}.".format(id))
            raise falcon.HTTPUnprocessableEntity(title="Uprocessable entlity", description="Failed while getting invoices.")


class InvoiceDeleteEndpoint:
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

                invoice = session.query(Invoice).filter(Invoice.id == id).first()

                if invoice is None:
                    raise falcon.HTTPNotFound(title="Invoice Not Found")

                if invoice.is_deleted():
                    falcon.HTTPNotFound("Invoice does not exist.")

                invoice.delete(session)
                resp.body = json.dumps(invoice.to_dict(), default=str)
        except:
            logger.exception("Error, Failed to delete invoice with ID {}.".format(id))
            raise falcon.HTTPBadRequest(title="Error", description="Failed to delete invoice with ID {}.".format(id))


class InvoiceExportToExcelEndpoint:
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
                try:
                    consultant_id = None
                    parlour = None
                    consultant = None

                    if "status" in req.params:
                        status = req.params.pop("status")

                    if "consultant_id" in req.params:
                        consultant_id = req.params.pop("consultant_id")

                    if consultant_id:
                        consultant = session.query(Consultant).filter(
                            Consultant.state == Consultant.STATE_ACTIVE,
                            Consultant.id == consultant_id
                        ).one()

                    parlour = session.query(Parlour).filter(
                        Parlour.state == Parlour.STATE_ACTIVE,
                        Parlour.id == id
                    ).one_or_none()
                except MultipleResultsFound as e:
                    raise falcon.HTTPBadRequest(title="Error", description="Error getting applicants")

                if not parlour:
                    parlour = consultant.parlour

                current_time = datetime.utcnow()
                current_week = current_time - timedelta(days=7)

                if consultant:
                    applicants = session.query(Applicant).filter(
                        Applicant.state == Applicant.STATE_ACTIVE,
                        Applicant.consultant_id == consultant.id
                    ).all()

                applicant_ids = [applicant.id for applicant in applicants]
                payments = session.query(Payment).filter(
                    Payment.state == Payment.STATE_ACTIVE,
                    Payment.date > current_week,
                    Payment.applicant_id.in_(applicant_ids)
                ).all()

                payment_ids = [payment.id for payment in payments]
                invoices = session.query(Invoice).filter(
                    Invoice.parlour_id == parlour.id,
                    Invoice.state == Invoice.STATE_ACTIVE,
                    Invoice.payment_id.in_(payment_ids)
                ).all()

                results = []
                for invoice in invoices:
                    applicant = invoice.payment.applicant

                    try:
                        main_member = session.query(MainMember).filter(
                            MainMember.state == MainMember.STATE_ACTIVE,
                            MainMember.applicant_id == applicant.id
                        ).one()

                    except NoResultFound:
                        continue
                    d = main_member.to_dict()
                    d.update({'assisted_by': invoice.assisted_by, 'payment_date': invoice.created, 'number_of_months': invoice.number_of_months})
                    results.append(d)

                if results:
                    data = []
                    for res in results:
                        applicant = res.get('applicant')
                        plan = applicant.get('plan')
                        underwriter = float(plan.get('underwriter_premium')) if plan.get('underwriter_premium') else None
                        amount = float(plan.get('premium')) * int(res.get('number_of_months'))
                        data.append({
                            'First Name': res.get('first_name'),
                            'Last Name': res.get('last_name'),
                            'ID Number': res.get('id_number') if res.get('id_number') else res.get('date_of_birth'),
                            'Status': applicant.get('status') if res.get else None,
                            'Premium': float(plan.get('premium')),
                            'Amount': amount,
                            'Number of Months': int(res.get('number_of_months')),
                            'Assisted By': res.get('assisted_by'),
                            'Payment Date': res.get('payment_date')
                            })

                    df = pd.DataFrame(data)
                    filename = '{}_{}'.format(invoice.assisted_by, invoice.payment_date)
                    writer = pd.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter')
                    df.to_excel(writer, sheet_name='Sheet1', index=False)
                    os.chdir('./assets/uploads/spreadsheets')
                    path = os.getcwd()
                    writer.save()
                    os.chdir('../../..')

                    with open('{}/{}.xlsx'.format(path, filename), 'rb') as f:
                        resp.downloadable_as = '{}.xls'.format(filename)
                        resp.content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        resp.stream = [f.read()]
                        resp.status = falcon.HTTP_200

        except Exception as e:
            logger.exception("Error, Failed to get Applicants for user with ID {}.".format(id))
            raise e
