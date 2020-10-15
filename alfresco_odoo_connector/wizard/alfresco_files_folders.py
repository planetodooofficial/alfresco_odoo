from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import base64
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class Folder(models.Model):
    """This class contains all the folder's that are created in Alfresco Repository."""
    _name = 'folder.details'

    name = fields.Char('Folders')
    folder_id = fields.Char('Id')


class Manage_Files_Folders(models.TransientModel):
    """This class contains all the functionality for managing files &
    folder in the Alfresco Repository"""

    _name = 'alfresco.files.folder'
    _rec_name = 'alf_folder_name'

    alf_folder_name = fields.Char("Folder Name")
    alf_folder_title = fields.Char("Folder Title")
    alf_folder_desc = fields.Char("Folder Description")
    alf_folder_path = fields.Char(string="Relative Path")

    alf_file = fields.Many2many(comodel_name="ir.attachment", relation="m2m_ir_attachment_relation",
                                column1="m2m_id", column2="attachment_id", string="Upload Files")
    alf_file_name = fields.Char("File Name")
    alf_file_title = fields.Char("File Title")
    alf_file_description = fields.Char("File Description")

    alf_search_folder = fields.Many2one('folder.details', string="Select Folder")
    alf_relative_path = fields.Char('Relative Path')

    @api.model
    def default_get(self, default_field):
        res = super(Manage_Files_Folders, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
            text = str(res['alf_relative_path'])
            t = text.split("/")
            new_path = '/' + t[1] + '/' + self.env.cr.dbname + '/' + t[2] + '/'
            res.update({
                'alf_relative_path': str(new_path)
            })
        if self._context.get('sale_id'):
            res['alf_folder_path'] = self._context.get('sale_id')
        return res

    def create_folder(self):
        """This function is to create folders in your root directory."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        datas = {
            "name": self.alf_folder_name,
            "nodeType": "cm:folder",
            "relativePath": "",
            "properties":
                {
                    "cm:title": self.alf_folder_title,
                    "cm:description": self.alf_folder_desc
                }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if datas['name'] is False:
            datas.update({'name': 'Odoo'})
        if datas['name'] is 'Odoo':
            datas.update({'name': 'Sale Orders', 'relativePath': '/Odoo'})
        if datas['name'] is 'Sale Orders':
            datas.update({'name': 'SO001', 'relativePath': '/Odoo/Sale Orders'})

        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        data = json.loads(response.text)
        if data['entry']['name'] is 'Odoo':
            self.create_folder()
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

    def update_folder(self):
        """This function is to update folder name in your root directory."""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        folder = self.env['folder.details'].search([('name', '=', self.alf_search_folder.name)])

        datas = {
            "name": self.alf_folder_name,
            "nodeType": "cm:folder",
            "properties":
                {
                    "cm:title": self.alf_folder_title,
                    "cm:description": self.alf_folder_desc
                }
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/' + str(
            folder.folder_id)

        response = requests.put(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)

            # This is to check if the folder exist. If the folder exist, it will write the new name of the folder
            # if the folder is not there, it will create a new record with the respective folder name.

            existing_folder = self.env['folder.details'].search([('folder_id', '=', data['entry']['id'])])
            existing_folder.write({'name': data['entry']['name'],
                                   'folder_id': data['entry']['id']})

            # This Wizard is use to display the information which we are getting in Response.

            wiz_ob = self.env['pop.folder'].create(
                {'pop_up': "Folder" + " " + data["entry"]["name"] + " " + "has been updated"})
            return {
                'name': _('Update Folder'),
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
                'name': _('Update Folder'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.folder',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }

    def update_folder_cron(self):
        """This function will list all the folder in the Repository"""
        """Also It will be used in "ir.cron" to update the folder list in Odoo Database with folder list from Alfresco Repository"""

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        if ticket.alf_encoded_ticket:
            pass
        else:
            raise ValidationError(_("Please Login!!!"))

        base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children?fields=nodeType,name&skipCount=0&maxItems=100&include=id&orderBy=name ASC'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        response = requests.get(base_url, headers=headers)
        list_content = json.loads(response.text)
        if response.status_code == 200:
            folder_search = self.env['folder.details'].search([])
            folder_list = []
            content = list_content['list']['entries']
            for i in content:
                folder_list.append(i['entry']['id'])
            if folder_search:
                for folder in folder_search:
                    if folder.folder_id not in folder_list:
                        folder.unlink()
                        self._cr.commit()
            else:
                wiz_ob = self.env['pop.list.content'].create(
                    {'popup_list_content': "Folders doesn't exist!"})
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
            # wiz_ob = self.env['pop.list.content'].create({'popup_list_content': 'Folder List Updated Successfully!'})
            # return {
            #     'name': _('Alert'),
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'res_model': 'pop.list.content',
            #     'res_id': wiz_ob.id,
            #     'view_id': False,
            #     'target': 'new',
            #     'views': False,
            #     'type': 'ir.actions.act_window',
            # }

    # def filter_contents_of_folder(self):
    #     """This function will list the contents of a folder in the repository"""
    #
    #     ticket = self.env['alfresco.operations'].search([], limit=1)
    #     ticket.get_auth_token_header()

    # if ticket.alf_encoded_ticket:
    #     pass
    # else:
    #     raise ValidationError(_("Please Login!!!"))
    #
    #     base_url = ticket.alf_base_url + "alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children?relativePath=Test&orderBy=name%20DESC"
    #
    #     headers = {
    #         'Accept': 'application/json',
    #         'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
    #     }
    #
    #     response = requests.get(base_url, headers=headers)

    # def get_folder_file_metadata(self):
    #     """Getting the metadata for a node returns the properties for the node type and applied aspects."""
    #
    #     ticket = self.env['alfresco.operations'].search([], limit=1)
    #     ticket.get_auth_token_header()
    # if ticket.alf_encoded_ticket:
    #     pass
    # else:
    #     raise ValidationError(_("Please Login!!!"))
    #
    #     base_url = ticket.alf_base_url + 'alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-'
    #
    #     headers = {
    #         'Accept': 'application/json',
    #         'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
    #     }
    #
    #     response = requests.get(base_url, headers=headers)
    #     print(json.loads(response.text))

    def upload_file(self):
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
                'relativePath': (None, self.alf_relative_path + self.alf_folder_path),
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
