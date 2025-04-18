from odoo import models, fields

class SaleChannel(models.Model):
    _name = "sale.channel"
    _description = "Canal de venta externo"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Código único", required=True, help="Código usado por APIs externas")
    active = fields.Boolean(default=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    external_channel_id = fields.Many2one("sale.channel", string="Canal externo")
    external_order_ref = fields.Char("Referencia externa")
    synced_from_api = fields.Boolean("Sincronizado vía API", default=False)
