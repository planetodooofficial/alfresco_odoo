from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import requests
import json


class A1(models.Model):
    _inherit = ['sale.order']

    notebook_ids = fields.One2many('testing', 'main_class_id', string="Test B2")
    search_folder = fields.Many2one('folder.details', string="Folders")


class A3(models.Model):
    _name = 'testing.ui'

    notebook_ids = fields.One2many('testing', 'main_class_id', string="Test B2")
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

            result = self._cr.execute('delete from testing')

            if response_data['list']['pagination']['count'] >= 1:
                for record in response_data['list']['entries']:
                    if record['entry']['name']:
                        name = record['entry']['name']
                        doc_id = record['entry']['id']
                        document_vals = [(0, 0, {
                            'main_class_id': self.id,
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


class A2(models.Model):
    _name = 'testing'

    main_class_id = fields.Many2one('testing.ui', string="Test A1")
    document_name = fields.Char("Name")
    document_id = fields.Char("ID")

    def delete_files(self):
        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        ui_call = self.env['testing.ui'].search([], limit=1)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
        }

        download_file_url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            self.document_id)

        response_get_id = requests.delete(download_file_url, headers=headers)
        if response_get_id.status_code == 204:
            ui_call.save_document_content()
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

        url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(self.document_id) + '/content'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self'
            }
        else:
            raise ValidationError(_("Please check your request and try again!"))
