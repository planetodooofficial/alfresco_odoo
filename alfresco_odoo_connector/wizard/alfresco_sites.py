from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
import base64

_logger = logging.getLogger(__name__)


class Sites(models.Model):
    _name = 'sites.details'

    name = fields.Char('Site Name')
    site_id = fields.Char('Site ID')
    site_document_id = fields.Char('Site Document Id')


class ManagingSites(models.TransientModel):
    _name = 'manage.sites'

    alf_site_name = fields.Char("Site Name")
    alf_site_description = fields.Char("Site Description")
    alf_site_visibility = fields.Selection([('PUBLIC', 'PUBLIC'), ('PRIVATE', 'PRIVATE'), ('MODERATED', 'MODERATED')],
                                           string="Site Visibility")

    alf_site_search = fields.Many2one('sites.details', string="Select Site")

    alf_site_upload_content = fields.Binary(string='Upload Content')
    alf_site_file_name = fields.Char("File Name")

    def create_site(self):
        """This function Creates an Alfresco Share site."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = ticket.alf_base_url + '/alfresco/api/-default-/public/alfresco/versions/1/sites'

        datas = {
            "title": self.alf_site_name,
            "description": self.alf_site_description,
            "visibility": self.alf_site_visibility
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201:
            data = json.loads(response.text)

            # This is to check if the site exist. If the folder exist, it will write the new name of the site
            # if the site is not there, it will create a new record with the respective site name.

            self.env['sites.details'].create({'name': data['entry']['title'],
                                              'site_id': data['entry']['id']})

            # This Wizard is use to display the information which we are getting in Response.

            wiz_ob = self.env['site'].create(
                {'pop_up': 'Your site' + " " + data['entry']['title'] + " " + 'has been created.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        elif response.status_code == 401:
            wiz_ob = self.env['site'].create(
                {'pop_up': 'Authentication Failed.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        elif response.status_code == 409:
            wiz_ob = self.env['site'].create(
                {'pop_up': 'Site with the given identifier already exists.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }

    def update_site(self):
        """This function Updates the metadata for an Alfresco Share site."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        sites = self.env['sites.details'].search([('name', '=', self.alf_site_search.name)])

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        datas = {
            "title": str(self.alf_site_name),
            "description": str(self.alf_site_description),
            "visibility": str(self.alf_site_visibility)
        }

        url = ticket.alf_base_url + '/alfresco/api/-default-/public/alfresco/versions/1/sites/' + str(
            sites.site_id)

        response = requests.put(url, data=json.dumps(datas), headers=headers)
        data = json.loads(response.text)
        if response.status_code == 200:

            # This is to check if the site exist. If the folder exist, it will write the new name of the site
            # if the site is not there, it will create a new record with the respective site name.

            existing_site = self.env['sites.details'].search([('site_id', '=', data['entry']['id'])])
            existing_site.write({'name': data['entry']['title'],
                                 'site_id': data['entry']['id']})

            # This Wizard is use to display the information which we are getting in Response.

            wiz_ob = self.env['site'].create({'pop_up': 'Site with the given identifier updated successfully.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        if response.status_code == 401:
            wiz_ob = self.env['site'].create(
                {'pop_up': 'Authentication failed.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
        if response.status_code == 404:
            wiz_ob = self.env['site'].create(
                {'pop_up': 'This siteId' + " " + str(data['entry']['id']) + " " + 'does not exist.'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'site',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }

    def add_content_to_site(self):
        """This function Creates folders and add files to an Alfresco Share site's Document Library."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        sites = self.env['sites.details'].search([('name', '=', self.alf_site_search.name)])

        document_lib_url = ticket.alf_base_url + '/alfresco/api/-default-/public/alfresco/versions/1/sites/' + sites.site_id + '/containers/documentLibrary'

        document_lib_headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response_doc = requests.get(document_lib_url, headers=document_lib_headers)
        data_doc = json.loads(response_doc.text)
        if response_doc.status_code == 200:

            # This is to check if the site exist. If the folder exist, it will write the new name of the site
            # if the site is not there, it will create a new record with the respective site name.

            existing_site = self.env['sites.details'].search([('site_id', '=', sites.site_id)])
            existing_site.write({'name': sites.name,
                                 'site_id': sites.site_id,
                                 'site_document_id': data_doc['entry']['id']})

        url = ticket.alf_base_url + '/api/-default-/public/alfresco/versions/1/nodes/' + str(
            sites.site_document_id) + '/children'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        datas = {
            "name": "My" + " " + sites.name + " " + "Stuff",
            "nodeType": "cm:folder"
        }

        response_entry = requests.post(url, data=json.dumps(datas), headers=headers)
        data = json.loads(response_entry.text)
        site_folder_id = False
        if response_entry.status_code == 200:
            site_folder_id = data['entry']['id']

        data_file = base64.b64decode(self.alf_site_upload_content)

        site_url = ticket.alf_base_url + '/api/-default-/public/alfresco/versions/1/nodes/' + site_folder_id + '/children'

        file_header = {
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        files = {
            'filedata': data_file,
            'name': (None, self.alf_site_file_name),
            'nodeType': (None, 'cm:content'),
        }

        response = requests.post(site_url, headers=file_header, files=files)
        print(response)

    def add_members_to_site(self):
        """This function add members to an Alfresco Share site."""
