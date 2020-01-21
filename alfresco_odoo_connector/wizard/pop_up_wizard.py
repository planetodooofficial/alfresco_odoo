
from odoo import api, fields, models, _, tools


class PopMessages(models.TransientModel):
    _name = 'pop.messages'

    popup_text = fields.Char('Your email has been sent.', readonly=True)
