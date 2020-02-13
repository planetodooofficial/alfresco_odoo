from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import base64
import logging
import sqlite3
import requests
import json


class A1(models.Model):
    _inherit = ['sale.order']

    notebook_ids = fields.One2many('testing', 'main_class_id', string="Test B2")
    search_folder = fields.Many2one('folder.details', string="Folders")


class A3(models.Model):
    _name = 'testing.ui'

    notebook_ids = fields.One2many('testing', 'main_class_id', string="Test B2")
    search_folder = fields.Many2one('folder.details', string="Folders")

    # @api.onchange('search_folder')
    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.search_folder.name)])

        get_file_url = str(ticket.alf_base_url) + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' \
                       + str(folder.folder_id) + '/children'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(get_file_url, headers=headers)
        response_data = json.loads(response.text)

        result = self._cr.execute('delete from testing')

        if response_data['list']['pagination']['count'] >= 1:
            for record in response_data['list']['entries']:
                if record['entry']['name']:
                    name = record['entry']['name']
                    document_vals = [(0, 0, {
                        'main_class_id': self.id,
                        'document_name': name
                    })]
                    existing = self.notebook_ids.search([('document_name', '=', name)])
                    if existing:
                        existing.write({'document_name': name})
                    else:
                        self.update({'notebook_ids': document_vals})
                        self._cr.commit()
    #         raise ValidationError(_("Files Exported Successfully!"))
    #     else:
    #         raise ValidationError(_("!BLANK!"))
    #
    # def delete_files(self):
    #
    #     ticket = self.env['alfresco.operations'].search([], limit=1)
    #     ticket.get_auth_token_header()
    #
    #     url = str(ticket.alf_base_url) + '/alfresco/api/-default-/public/alfresco/versions/1/nodes/'


class A2(models.Model):
    _name = 'testing'

    main_class_id = fields.Many2one('testing.ui', string="Test A1")
    document_name = fields.Char("Document Name")
