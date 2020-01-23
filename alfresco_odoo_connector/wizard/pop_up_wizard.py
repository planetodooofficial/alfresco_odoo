
from odoo import api, fields, models, _, tools


class PopMessages(models.TransientModel):
    _name = 'pop.messages'

    popup_text = fields.Char("String", readonly=True)


class PopUpListContent(models.TransientModel):
    _name = 'pop.list.content'

    popup_list_content = fields.Char("Pop Up", readonly=True)


class PopUpFileCreateMsg(models.TransientModel):
    _name = 'file.msg'

    pop_up = fields.Char("Pop Up", readonly=True)