from odoo import api, fields, models, _, tools
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
    alf_base_url = fields.Char("Alfresco URL", store=True)

    def get_auth_token_header(self):

        """Function for Authenticating with the Repository to get a TICKET
        and generate TOKEN which will be use for other API calls"""

        datas = {
            "userId": self.alf_username,
            "password": self.alf_password
        }

        try:
            auth_url = self.alf_base_url + '/alfresco/api/-default-/public/authentication/versions/1/tickets'
            ticket_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Basic'
            }
            response = requests.post(auth_url, data=json.dumps(datas), headers=ticket_headers)
            if response.status_code == 201:
                new_ticket = json.loads(response.text)
                ticket = new_ticket['entry']['id']
                self.alf_ticket = ticket
                auth_token = base64.b64encode(str(self.alf_ticket).encode('utf-8')).decode()
                if auth_token:
                    self.alf_encoded_ticket = auth_token

                wiz_ob = self.env['pop.auth'].create(
                    {'pop_up': 'Your Ticket' + " " + '*' + self.alf_ticket + '*' + " " + 'has been generated.'})
                return {
                    'name': _('Authentication'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.auth',
                    'res_id': wiz_ob.id,
                    'view_id': False,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                }
            elif response.status_code == 403:
                wiz_ob = self.env['pop.auth'].create(
                    {'pop_up': 'Login Failed! Please try again.'})
                return {
                    'name': _('Authentication'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.auth',
                    'res_id': wiz_ob.id,
                    'view_id': False,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                }
            else:
                wiz_ob = self.env['pop.auth'].create(
                    {'pop_up': 'Please check your request and try again!'})
                return {
                    'name': _('Authentication'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.auth',
                    'res_id': wiz_ob.id,
                    'view_id': False,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                }

        except Exception as e:
            raise e

    def get_repository_info(self):

        """This function is use to Get the information of the Alfresco Repository"""

        repo_url = self.alf_base_url + '/alfresco/api/discovery'

        token_headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + self.alf_encoded_ticket
        }

        response = requests.get(repo_url, headers=token_headers)
        if response.status_code == 200:
            response_text = json.loads(response.text)
            if response_text['entry']['repository']['edition'] == 'Community':
                wiz_ob = self.env['pop.messages'].create(
                    {'popup_edition': 'Edition: ' + response_text['entry']['repository']['edition'],
                     'popup_version': 'Version: ' + 'v' + response_text['entry']['repository']['version'][
                         'major'] + '.' +
                                      response_text['entry']['repository']['version']['minor'] + '.' +
                                      response_text['entry']['repository']['version']['patch'] + '.' +
                                      response_text['entry']['repository']['version']['hotfix'],
                     })
            else:
                wiz_ob = self.env['pop.messages'].create(
                    {'popup_edition': 'Edition: ' + response_text['entry']['repository']['edition'],
                     'popup_version': 'Version: ' + 'v' + response_text['entry']['repository']['version'][
                         'major'] + '.' +
                                      response_text['entry']['repository']['version']['minor'] + '.' +
                                      response_text['entry']['repository']['version']['patch'] + '.' +
                                      response_text['entry']['repository']['version']['hotfix'],
                     'popup_license': 'License: ' + response_text['entry']['repository']['license']['holder'],
                     'popup_license_issued_at': 'Issued At: ' + response_text['entry']['repository']['license'][
                         'issuedAt'],
                     'popup_license_issued_till': 'Issued Till: ' + response_text['entry']['repository']['license'][
                         'expiresAt'],
                     'popup_license_days': 'Remaining Days: ' + str(
                         response_text['entry']['repository']['license']['remainingDays'])
                     })
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
            wiz_ob1 = self.env['pop.messages'].create({'popup_edition': 'Please check your request and try again!'})
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
