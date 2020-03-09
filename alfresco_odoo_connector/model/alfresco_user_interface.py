import base64

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import requests
import json


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    notebook_ids = fields.One2many('alf.ui.functionality', 'sale_order_id', string="Documents List")
    search_folder = fields.Many2one('folder.details', string="Folder")
    active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Sales Order/')
    attachment_count = fields.Integer('Count')

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.search_folder.name)])

        get_file_url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            folder.folder_id) + '/children'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(get_file_url, headers=headers)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            self.attachment_count = response_data['list']['pagination']['count']

            result = self._cr.execute('delete from alf_ui_functionality')

            if response_data['list']['pagination']['count'] >= 1:
                for record in response_data['list']['entries']:
                    if record['entry']['name']:
                        name = record['entry']['name']
                        doc_id = record['entry']['id']
                        document_vals = [(0, 0, {
                            'sale_order_id': self.id,
                            'document_name': name,
                            'document_id': doc_id
                        })]
                        existing = self.notebook_ids.search([('document_id', '=', doc_id),
                                                             ('document_name', '=', name)])
                        if existing:
                            existing.write({
                                'document_name': name,
                                'document_id': doc_id
                            })
                        else:
                            self.update({'notebook_ids': document_vals})
                            self._cr.commit()
                wiz_ob = self.env['pop.auth'].create(
                    {'pop_up': 'Files Exported Successfully.'})
                return {
                    'name': _('Refresh Repository'),
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
                    {'pop_up': 'Folder does not contains any files.'})
                return {
                    'name': _('Refresh Repository'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.auth',
                    'res_id': wiz_ob.id,
                    'view_id': False,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                }

    def create_folders(self):
        """This function is to create folder inside folder inside root folder into root directory."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        datas = {
            "name": "",
            "nodeType": "cm:folder",
            "relativePath": "",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        data_response_2 = False

        if not datas['name']:
            datas.update({'name': 'Odoo'})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Sales Order', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Sales Order':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Sales Order'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                               'folder_id': data_response_2['entry']['id']})
            if self.active is False:
                self.update({'active': True})

            # This Wizard is use to display the information which we are getting in Response.

            wiz_ob = self.env['pop.folder'].create(
                {'pop_up': "Folder Created"})
            return {
                'name': _('Create Folder'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.folder',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }

        elif response.status_code == 409:
            data_response_2 = json.loads(response_2.text)
            wiz_ob = self.env['pop.folder'].create({'pop_up': data_response_2["error"]["errorKey"]})
            return {
                'name': _('Create Folder'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.folder',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        else:
            wiz_ob = self.env['pop.folder'].create({'pop_up': "Please check your request and try again!"})
            return {
                'name': _('Create Folder'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.folder',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }


# class PurchaseOrderInherit(models.Model):
#     _inherit = 'purchase.order'
#
#     notebook_ids = fields.One2many('alf.ui.functionality', 'id', string="")
#     search_folder = fields.Many2one('folder.details', string="Folder")
#
#     def save_document_content(self):
#
#         ticket = self.env['alfresco.operations'].search([], limit=1)
#         ticket.get_auth_token_header()
#
#         folder = self.env['folder.details'].search([('name', '=', self.search_folder.name)])
#
#         get_file_url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
#             folder.folder_id) + '/children'
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
#         }
#
#         response = requests.get(get_file_url, headers=headers)
#         if response.status_code == 200:
#             response_data = json.loads(response.text)
#
#             result = self._cr.execute('delete from alf_ui_functionality')
#
#             if response_data['list']['pagination']['count'] >= 1:
#                 for record in response_data['list']['entries']:
#                     if record['entry']['name']:
#                         name = record['entry']['name']
#                         doc_id = record['entry']['id']
#                         document_vals = [(0, 0, {
#                             'id': self.id,
#                             'document_name': name,
#                             'document_id': doc_id
#                         })]
#                         existing = self.notebook_ids.search([('document_id', '=', doc_id),
#                                                              ('document_name', '=', name)])
#                         if existing:
#                             existing.write({
#                                 'document_name': name,
#                                 'document_id': doc_id
#                             })
#                         else:
#                             self.update({'notebook_ids': document_vals})
#                             self._cr.commit()
#                 wiz_ob = self.env['pop.auth'].create(
#                     {'pop_up': 'Files Exported Successfully.'})
#                 return {
#                     'name': _('Refresh Repository'),
#                     'view_type': 'form',
#                     'view_mode': 'form',
#                     'res_model': 'pop.auth',
#                     'res_id': wiz_ob.id,
#                     'view_id': False,
#                     'target': 'new',
#                     'views': False,
#                     'type': 'ir.actions.act_window',
#                 }
#             else:
#                 wiz_ob = self.env['pop.auth'].create(
#                     {'pop_up': 'Folder does not contains any files.'})
#                 return {
#                     'name': _('Refresh Repository'),
#                     'view_type': 'form',
#                     'view_mode': 'form',
#                     'res_model': 'pop.auth',
#                     'res_id': wiz_ob.id,
#                     'view_id': False,
#                     'target': 'new',
#                     'views': False,
#                     'type': 'ir.actions.act_window',
#                 }


class AlfrescoUIFunctionality(models.Model):
    _name = 'alf.ui.functionality'

    sale_order_id = fields.Many2one('sale.order', string="ID")
    document_name = fields.Char("Doc Name")
    document_id = fields.Char("Doc ID")

    def delete_files(self):
        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        call = self.env['sale.order'].search([], limit=1)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
        }

        download_file_url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            self.document_id)

        response_get_id = requests.delete(download_file_url, headers=headers)
        if response_get_id.status_code == 204:
            call.save_document_content()
            wiz_ob = self.env['pop.auth'].create(
                {'pop_up': 'Your file has been deleted.'})
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

    def download_files(self):
        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
        }

        url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            self.document_id) + '/content'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new'
            }
        else:
            raise ValidationError(_("Please check your request and try again!"))
