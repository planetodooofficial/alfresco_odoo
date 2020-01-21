from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class Manage_Files_Folders(models.TransientModel):
    """This class contains all the functionality for managing files &
    folder in the Alfresco Repository"""

    _name = 'alfresco.files.folder'
    _rec_name = 'alf_folder_name'

    alf_folder_name = fields.Char("Folder Name")
    alf_folder_title = fields.Char("Folder Title")
    alf_file_name = fields.Char("File Name")
    alf_folder_desc = fields.Char("Folder Description")

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
        print(response)
        #Listing is left on wizard

    def filer_contents_of_folder(self):
        """This function will list the contents of a folder in the repository"""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = "https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children?relativePath=Test&orderBy=name%20DESC"

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(base_url, headers=headers)
        print(response)
        # Listing is left on wizard and folder is Test over here

    def get_folder_file_metadata(self):
        """Getting the metadata for a node returns the properties for the node type and applied aspects."""

        ticket = self.env['alfresco.operations'].search([], limit=1)

        base_url = 'https://afvdpi.trial.alfresco.com/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic' + " " + str(ticket.alf_encoded_ticket)
        }

        response = requests.get(base_url, headers=headers)
        print(response)
