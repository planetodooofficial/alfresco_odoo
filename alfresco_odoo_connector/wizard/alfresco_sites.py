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

    alf_site_name = fields.Char("Site Name", required=True)
    alf_site_description = fields.Char("Site Description")
    alf_site_visibility = fields.Selection([('PUBLIC', 'PUBLIC'), ('PRIVATE', 'PRIVATE'), ('MODERATED', 'MODERATED')],
                                           string="Site Visibility", required=True)

    alf_site_search = fields.Many2one('sites.details', string="Select Site", required=True)

    alf_site_upload_content = fields.Binary(string='Upload Content')
    alf_site_file_name = fields.Char("File Name")

    def create_site(self):
        """This function Creates an Alfresco Share site."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/sites'

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
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

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

        url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/sites/' + str(
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
        ticket.get_auth_token_header()

        site_folder_id = False
        data = False

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        sites = self.env['sites.details'].search([('name', '=', self.alf_site_search.name)])

        document_lib_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/sites/' + sites.site_id + '/containers/documentLibrary'

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

        url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            sites.site_document_id) + '/children'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        datas = {
            "name": "My" + " " + sites.name + " " + "Stuff",
            "nodeType": "cm:folder"
        }

        result = requests.get(url, headers=headers)
        result_text = json.loads(result.text)
        if result_text['list']['pagination']['count'] >= 1:
            data = result_text['list']['entries'][0]['entry']['id']

        if data:
            if result.status_code == 200:
                site_folder_id = result_text['list']['entries'][0]['entry']['id']
        else:
            response_entry = requests.post(url, data=json.dumps(datas), headers=headers)
            data_post = json.loads(response_entry.text)
            if response_entry.status_code == 201:
                site_folder_id = data_post['entry']['id']

        data_file = base64.b64decode(self.alf_site_upload_content)

        site_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            site_folder_id if site_folder_id else data) + '/children'

        file_header = {
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        files = {
            'filedata': data_file,
            'name': (None, self.alf_site_file_name),
            'nodeType': (None, 'cm:content'),
        }

        response_upload_content = requests.post(site_url, headers=file_header, files=files)
        if response_upload_content.status_code == 201:
            wiz_ob = self.env['site'].create({'pop_up': 'Your content has been uploaded on the selected site'})
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

    def update_site_cron(self):
        """This function update Sites in Odoo Database with sites from Alfresco Repository."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/sites'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        response = requests.get(base_url, headers=headers)
        list_content = json.loads(response.text)
        if response.status_code == 200:
            site_search = self.env['sites.details'].search([])
            site_list = []
            content = list_content['list']['entries']
            for i in content:
                site_list.append(i['entry']['id'])
            if site_search:
                for site in site_search:
                    if site.site_id not in site_list:
                        site.unlink()
                        self._cr.commit()
            else:
                raise ValidationError(_("There are no sites in the repository"))
            wiz_ob = self.env['pop.list.content'].create({'popup_list_content': 'Site List Updated Successfully!'})
            return {
                'name': _('Alert'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.list.content',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }
