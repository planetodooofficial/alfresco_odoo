import base64
import csv
from tempfile import TemporaryFile
from io import StringIO

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
import os
import binascii
import codecs

_logger = logging.getLogger(__name__)


class Manage_Files_Folders(models.TransientModel):
    """This class contains all the functionality for managing files &
    folder in the Alfresco Repository"""

    _name = 'alfresco.files.folder'
    _rec_name = 'alf_folder_name'

    alf_folder_name = fields.Char("Folder Name")
    alf_folder_title = fields.Char("Folder Title")
    alf_folder_desc = fields.Char("Folder Description")

    alf_file = fields.Binary("Upload a File")
    alf_file_name = fields.Char("File Name")
    alf_file_title = fields.Char("File Title")
    alf_file_description = fields.Char("File Description")

    def create_folder(self):
        """This function is to create folders in your root directory."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        datas = {
            "name": str(self.alf_folder_name),
            "nodeType": "cm:folder",
            "properties":
                {
                    "cm:title": str(self.alf_folder_title),
                    "cm:description": str(self.alf_folder_desc)
                }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201:
            wiz_ob = self.env['pop.folder'].create(
                {'pop_up': "Folder" + json.loads(response.text)["entry"]["name"] + "been created"})
            return {
                'name': _('Alert'),
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

        list_of_id = []

        ticket = self.env['alfresco.operations'].search([], limit=1)

        url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-'

        datas = {
            "name": str(self.alf_folder_name),
            "nodeType": "cm:folder",
            "properties":
                {
                    "cm:title": str(self.alf_folder_title),
                    "cm:description": str(self.alf_folder_desc)
                }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response_get_id = requests.get(url, headers=headers)
        text = json.loads(response_get_id.text)
        get_id = text['list']['entries']
        for rec in get_id:
            list_of_id.append(rec['entry']['id'])

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/' + \
                   list_of_id[1]

        response = requests.put(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 200:
            print((json.loads(response.text)["entry"]["name"]))

    def list_contents_for_folders(self):
        """This function will list all the content of the folder in the Repository"""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children?fields=nodeType,name&skipCount=0&maxItems=100'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(base_url, headers=headers)
        list_content = json.loads(response.text)
        if response.status_code == 200:
            wiz_ob = self.env['pop.list.content'].create(
                {'popup_list_content': list_content['list']['pagination']['totalItems']})
            return {
                'name': _('Content of Repository'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.list.content',
                'res_id': wiz_ob.id,
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
            }

    def filter_contents_of_folder(self):
        """This function will list the contents of a folder in the repository"""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = "https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children?relativePath=Test&orderBy=name%20DESC"

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(base_url, headers=headers)

    def get_folder_file_metadata(self):
        """Getting the metadata for a node returns the properties for the node type and applied aspects."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(base_url, headers=headers)
        print(json.loads(response.text))

    def upload_file(self):
        """Uploading a file to the Repository means creating a node with metadata and content."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children'

        headers = {
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket),
        }

        data = base64.b64decode(self.alf_file)

        files = {
            'filedata': data,
            'name': (None, self.alf_file_name),
            'nodeType': (None, 'cm:content'),
            'cm:title': (None, 'My text'),
            'cm:description': (None, 'My text document description'),
            'relativePath': (None, '/Test'),
        }

        response = requests.post(base_url, headers=headers, files=files)
        if response.status_code == 201:
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
            wiz_ob = self.env['file.msg'].create({'pop_up': 'New name clashes with an existing file in the current folder.'})
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
        elif response.status_code == 401:
            wiz_ob = self.env['file.msg'].create({'pop_up': 'Authentication failed.'})
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
