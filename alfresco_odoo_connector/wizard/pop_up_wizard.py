from odoo import api, fields, models, _, tools


class PopMessages(models.TransientModel):
    _name = 'pop.messages'

    popup_edition = fields.Char("Edition", readonly=True)
    popup_version = fields.Char("Version", readonly=True)
    popup_license = fields.Char("License", readonly=True)
    popup_license_issued_at = fields.Char("Issued At", readonly=True)
    popup_license_issued_till = fields.Char("Issued To", readonly=True)
    popup_license_days = fields.Char("Remaining Days", readonly=True)


class PopAuth(models.TransientModel):
    _name = 'pop.auth'

    pop_up = fields.Char("String", readonly=True)


class PopUpListContent(models.TransientModel):
    _name = 'pop.list.content'

    popup_list_content = fields.Char("Pop Up", readonly=True)


class PopUpFolder(models.TransientModel):
    _name = 'pop.folder'

    pop_up = fields.Char("Pop Up", readonly=True)


class PopUpFileCreateMsg(models.TransientModel):
    _name = 'file.msg'

    pop_up = fields.Char("Pop Up", readonly=True)


class PopUpSite(models.TransientModel):
    _name = 'site'

    pop_up = fields.Char("Pop Up", readonly=True)
