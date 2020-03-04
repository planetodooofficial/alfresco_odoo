import base64

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import requests
import json


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    notebook_ids = fields.One2many('alf.ui.functionality', 'id', string="Documents List")
    search_folder = fields.Many2one('folder.details', string="Folder")

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

            result = self._cr.execute('delete from alf_ui_functionality')

            if response_data['list']['pagination']['count'] >= 1:
                for record in response_data['list']['entries']:
                    if record['entry']['name']:
                        name = record['entry']['name']
                        doc_id = record['entry']['id']
                        document_vals = [(0, 0, {
                            'id': self.id,
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


class Manage_Files_Folders(models.TransientModel):
    """This class contains all the functionality for managing files &
    folder in the Alfresco Repository"""

    _name = 'alfresco.files.folder'

    alf_folder_name = fields.Char("Folder Name")
    alf_folder_title = fields.Char("Folder Title")
    alf_folder_desc = fields.Char("Folder Description")
    alf_folder_path = fields.Many2one('folder.details', string="Relative Path")

    alf_file = fields.Many2many(comodel_name="ir.attachment", relation="m2m_ir_attachment_relation",
                                column1="m2m_id", column2="attachment_id", string="Upload Files")
    alf_file_name = fields.Char("File Name")
    alf_file_title = fields.Char("File Title")
    alf_file_description = fields.Char("File Description")

    alf_search_folder = fields.Many2one('folder.details', string="Select Folder")

    def folder_creation(self):
        """This function is to create folders in your root directory."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        datas = {
            "name": False,
            "nodeType": "cm:folder",
            "relativePath": False,
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if datas['name'] is False:
            datas.update({'name': 'Odoo'})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201:
            if datas['name'] is 'Odoo':
                datas.update({'name': 'Sale Orders', 'relativePath': '/Odoo'})
                response = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response.status_code == 201:
                    if datas['name'] is 'Sale Orders':
                        datas.update({'name': 'SO001', 'relativePath': '/Odoo/Sale Orders'})
                        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        data = json.loads(response.text)
        if response.status_code == 201:
            self.env['folder.details'].create({'name': data['entry']['name'],
                                               'folder_id': data['entry']['id']})

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
            wiz_ob = self.env['pop.folder'].create({'pop_up': data["error"]["errorKey"]})
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

    def upload_files(self):
        """Uploading a file to the Repository means creating a node with metadata and content."""

        response = False

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        headers = {
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        for file in self.alf_file:
            file_data = base64.b64decode(file.datas)

            files = {
                'filedata': file_data,
                'name': (None, file.display_name),
                'nodeType': (None, 'cm:content'),
                'relativePath': ("/Odoo/Sale Orders/" + self.alf_folder_path.name),
            }

            response = requests.post(base_url, headers=headers, files=files)
        if response.status_code == 201:

            # This Wizard is use to display the information which we are getting in Response.

            wiz_ob = self.env['file.msg'].create({'pop_up': 'Your file has been uploaded.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'file.msg',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        elif response.status_code == 409:
            wiz_ob = self.env['file.msg'].create(
                {'pop_up': 'New name clashes with an existing file in the current folder.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'file.msg',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        else:
            wiz_ob = self.env['file.msg'].create({'pop_up': 'Please check your request and try again!'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'file.msg',
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

    id = fields.Many2one('sale.order', string="ID")
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
                'target': 'self'
            }
        else:
            raise ValidationError(_("Please check your request and try again!"))
