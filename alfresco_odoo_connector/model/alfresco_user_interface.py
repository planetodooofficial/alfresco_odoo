import base64

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import requests
import json


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    notebook_ids = fields.One2many('alf.ui.functionality', 'sale_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Sales Order/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Sale Order ID')

    @api.model
    def default_get(self, default_field):
        res = super(SaleOrderInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrderInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['sale.order'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Sales Order/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
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
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    notebook_ids = fields.One2many('alf.ui.functionality', 'purchase_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Purchase Order/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Purchase Order ID')

    @api.model
    def default_get(self, default_field):
        res = super(PurchaseOrderInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(PurchaseOrderInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['purchase.order'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Purchase Order/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Purchase Order', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Purchase Order':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Purchase Order'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class InvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    notebook_ids = fields.One2many('alf.ui.functionality', 'invoice_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Invoices & Bills/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('ID')

    @api.model
    def default_get(self, default_field):
        res = super(InvoiceInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(InvoiceInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['account.invoice'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Invoices & Bills/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Invoices & Bills', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Invoices & Bills':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Invoices & Bills'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class LotInherit(models.Model):
    _inherit = 'stock.production.lot'

    notebook_ids = fields.One2many('alf.ui.functionality', 'stock_lot_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Stock Production Lot/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('LOT ID')

    @api.model
    def default_get(self, default_field):
        res = super(LotInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(LotInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['stock.production.lot'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Stock Production Lot/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Stock Production Lot', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Stock Production Lot':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Stock Production Lot'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class ContactsInherit(models.Model):
    _inherit = 'res.partner'

    notebook_ids = fields.One2many('alf.ui.functionality', 'contacts_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Contacts/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Contacts ID')

    @api.model
    def default_get(self, default_field):
        res = super(ContactsInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals_list):
        res = super(ContactsInherit, self).create(vals_list)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['res.partner'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Contacts/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Contacts', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Contacts':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Contacts'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class MaintenanceInherit(models.Model):
    _inherit = 'maintenance.request'

    notebook_ids = fields.One2many('alf.ui.functionality', 'maintenance_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Maintenance/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Maintenance ID')

    @api.model
    def default_get(self, default_field):
        res = super(MaintenanceInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(MaintenanceInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['maintenance.request'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Maintenance/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Maintenance', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Maintenance':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Maintenance'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class EquipmentInherit(models.Model):
    _inherit = 'maintenance.equipment'

    notebook_ids = fields.One2many('alf.ui.functionality', 'equipment_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Equipment/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Equipment ID')

    @api.model
    def default_get(self, default_field):
        res = super(EquipmentInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(EquipmentInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['maintenance.equipment'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Equipment/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Equipment', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Equipment':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Equipment'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    notebook_ids = fields.One2many('alf.ui.functionality', 'project_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Project Task/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Project Task ID')

    @api.model
    def default_get(self, default_field):
        res = super(ProjectTaskInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(ProjectTaskInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['project.task'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Project Task/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Project Task', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Project Task':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Project Task'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    notebook_ids = fields.One2many('alf.ui.functionality', 'employee_id', string="Documents List")
    is_active = fields.Boolean('Folder Created', default=False)
    relative_path = fields.Char('Path', default='/Odoo/Employee/')
    attachment_count = fields.Integer('Count')
    order_id = fields.Char('Employee ID')

    @api.model
    def default_get(self, default_field):
        res = super(EmployeeInherit, self).default_get(default_field)
        if self._context.get('path'):
            res['alf_relative_path'] = self._context.get('path')
        return res

    @api.model
    def create(self, vals):
        res = super(EmployeeInherit, self).create(vals)
        res.update({'order_id': res.name})
        return res

    def display_count_attachment(self):
        pass

    def save_document_content(self):

        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        folder = self.env['folder.details'].search([('name', '=', self.order_id)])

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
                            'order_id': self.id,
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

        res = self.env['hr.employee'].search([('id', '=', self.id)])
        res.write({'order_id': res.name})

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
            "relativePath": "/Odoo/Employee/",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic' + " " + ticket.alf_encoded_ticket
        }

        if not datas['name']:
            datas.update({'name': 'Odoo', 'relativePath': ''})
        response = requests.post(base_url, data=json.dumps(datas), headers=headers)
        if response.status_code == 201 or response.status_code == 409:
            if datas['name'] == 'Odoo':
                datas.update({'name': 'Employee', 'relativePath': '/Odoo'})
                response_1 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                if response_1.status_code == 201 or response_1.status_code == 409:
                    if datas['name'] == 'Employee':
                        datas.update({'name': str(self.name), 'relativePath': '/Odoo/Employee'})
                        response_2 = requests.post(base_url, data=json.dumps(datas), headers=headers)
                        if response_2.status_code == 201:
                            data_response_2 = json.loads(response_2.text)
                            self.env['folder.details'].create({'name': data_response_2['entry']['name'],
                                                               'folder_id': data_response_2['entry']['id']})
                            if self.is_active is False:
                                self.update({'is_active': True})
                        elif response_2.status_code != 201:
                            raise ValidationError(_('Folder name should not contain special characters.'))

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


class AlfrescoUIFunctionality(models.Model):
    _name = 'alf.ui.functionality'

    sale_id = fields.Many2one('sale.order', string="ID")
    purchase_id = fields.Many2one('purchase.order', string="ID")
    invoice_id = fields.Many2one('account.invoice', string='IDs')
    stock_lot_id = fields.Many2one('stock.production.lot', string='ID')
    maintenance_id = fields.Many2one('maintenance.request', string='ID')
    equipment_id = fields.Many2one('maintenance.equipment', string='ID')
    project_id = fields.Many2one('project.task', string='ID')
    contacts_id = fields.Many2one('res.partner', string='ID')
    employee_id = fields.Many2one('hr.employee', string='ID')
    document_name = fields.Char("Doc Name")
    document_id = fields.Char("Doc ID")

    def delete_files(self):
        ticket = self.env['alfresco.operations'].search([], limit=1)
        ticket.get_auth_token_header()

        call = self.env['sale.order'].search([], limit=1)
        call = self.env['purchase.order'].search([], limit=1)
        call = self.env['account.invoice'].search([], limit=1)
        call = self.env['stock.production.lot'].search([], limit=1)
        call = self.env['maintenance.request'].search([], limit=1)
        call = self.env['maintenance.equipment'].search([], limit=1)
        call = self.env['project.task'].search([], limit=1)
        call = self.env['res.partner'].search([], limit=1)
        call = self.env['hr.employee'].search([], limit=1)

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
