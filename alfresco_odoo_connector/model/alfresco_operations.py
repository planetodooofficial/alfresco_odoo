from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import base64
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class AlfrescoOperations(models.Model):
    _name = 'alfresco.operations'
    _rec_name = 'alf_username'

    alf_username = fields.Char("User ID")
    alf_password = fields.Char("Password")
    alf_ticket = fields.Char("Alfresco Ticket", readonly=True, store=True)
    alf_encoded_ticket = fields.Char("Alfresco Token", readonly=True, store=True)

    def get_auth_token_header(self):

        """Function for Authenticating with the Repository to get a TICKET
        and generate TOKEN which will be use for other API calls"""

        datas = {
            "userId": str(self.alf_username),
            "password": str(self.alf_password)
        }

        try:
            auth_url = "https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/authentication/versions/1/tickets"
            ticket_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Basic'
            }
            response = requests.post(auth_url, data=json.dumps(datas), headers=ticket_headers)
            if response.status_code == 201:
                new_ticket = json.loads(response.text)
                ticket = new_ticket['entry']['id']
                self.alf_ticket = str(ticket)

            auth_token = base64.b64encode(str(self.alf_ticket).encode('utf-8')).decode()
            if auth_token:
                self.alf_encoded_ticket = auth_token

        except Exception as e:
            raise e

    def get_repository_info(self):

        """This function is use to Get the information of the Repository"""

        repo_url = "https://afvdpi.trial.alfresco.com/alfresco/api/discovery"

        token_headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(self.alf_encoded_ticket)
        }

        response = requests.get(repo_url, headers=token_headers)
        if response.status_code == 200:
            wiz_ob = self.env['pop.messages'].create({'popup_text': 'Successful.'})
            return {
                'name': _('Repository Information'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.messages',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        else:
            wiz_ob1 = self.env['pop.messages'].create({'popup_text': 'Bad Response.'})
            return {
                'name': _('Repository Information'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.messages',
                'res_id': wiz_ob1.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }