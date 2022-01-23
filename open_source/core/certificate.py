from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

import os


class Certificate:
    can = None

    def __init__(self, file_name: str):
        os.chdir('./assets/uploads/certificates')

        self.y_position = 0
        self.file_path = "{}/{}.pdf".format(os.getcwd(), file_name)
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

        self.can = canvas.Canvas(self.file_path, pagesize=A4, bottomup=0)
        os.chdir('../../..')

    def get_file_path(self):
        return self.file_path

    def set_title(self, title: str):
        self.can.setFont('Helvetica-Bold', 16)
        self.can.drawCentredString(300, 60, title.title())

    def set_address(self, address: str):
        self.can.setFont('Helvetica', 10)
        self.can.drawCentredString(300, 75, address.title())

    def set_contact(self, contact: str):
        self.can.setFont('Helvetica', 10)
        self.can.drawCentredString(300, 90, contact)

    def set_email(self, email: str):
        self.can.setFont('Helvetica', 10)
        self.can.drawCentredString(300, 105, email.lower())

    def membership_certificate(self):
        self.can.setFont('Helvetica-Bold', 10)
        self.can.drawCentredString(300, 130, "Membership Certificate / Application Form")

    def set_member(self, member: str):
        self.can.setFont('Helvetica-Bold', 10)
        self.can.drawString(30, 180, member.title())

    def set_name(self, name: str):
        self.can.setFont('Helvetica', 10)
        self.can.drawString(30, 195, "Name: {}".format(name.title()))

    def set_id_number(self, id_number: str):
        self.can.drawString(30, 210, "ID Number: {}".format(id_number))

    def set_member_contact(self, contact: str):
        self.can.setFont('Helvetica', 10)
        self.can.drawString(30, 225, "Contact: {}".format(contact))

    def set_date_joined(self, date_joined):
        self.can.drawString(30, 240, "Date Joined: {}".format(date_joined))

    def set_date_created(self, date_created):
        self.can.drawString(30, 255, "Date Created: {}".format(date_created))

    def set_current_plan(self, plan: str):
        self.can.drawString(30, 270, "Current Plan: {}".format(plan.title()))

    def set_current_premium(self, premium):
        self.can.drawString(30, 285, "Premium: R{}".format(premium))

    def set_physical_address(self, address):
        self.y_position = 300
        self.can.drawString(30, 300, "Physical Address: {}".format(address))

    def add_other_members(self, member):
        self.can.setFont('Helvetica-Bold', 10)
        self.y_position = sum([self.y_position, 50])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "{}".format(member.type_text.title()))
        self.can.setFont('Helvetica', 10)
        self.y_position = sum([self.y_position, 15])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "Name: {} {}".format(member.first_name.title(), member.last_name.title()))
        self.y_position = sum([self.y_position, 15])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "DOB: {}".format(member.date_of_birth))
        self.y_position = sum([self.y_position, 15])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "Date joined: {}".format(member.date_joined))
        self.y_position = sum([self.y_position, 15])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "Relationship: {}".format(member.relation_text.title()))
        self.y_position = sum([self.y_position, 15])

        if self.y_position > 820:
            self.showPage()
            self.y_position = 60
        self.can.drawString(30, self.y_position, "Contact: {}".format(member.number))

    def set_relation(self, relation: str):
        self.can.drawString(30, 750, "Relationship: {}".format(relation.title()))

    def set_benefits(self, benefits):
        self.can.setFont('Helvetica-Bold', 10)
        self.y_position = sum([self.y_position, 50])
        self.can.drawString(30, self.y_position, "Benefits:")
        self.can.setFont('Helvetica', 10)

        for s in benefits.split("\n"):
            self.y_position = sum([self.y_position, 15])
            if len(s.split()) > 0:
                if self.y_position > 820:
                    self.showPage()
                    self.y_position = 60
                self.can.drawString(30, self.y_position, "- {}".format(s.replace("-", "").strip()))

    def showPage(self):
        self.can.showPage()

    def save(self):
        self.can.save()
