from odoo import models, fields

class SyncLog(models.Model):
    _name = "sync.log"
    _description = "Auditoría de pedidos sincronizados"

    name = fields.Char(default=lambda self: f"Log {fields.Datetime.now()}", readonly=True)
    channel_id = fields.Many2one("sale.channel", string="Canal")
    order_id = fields.Many2one("sale.order", string="Pedido")
    status = fields.Selection([("success", "Éxito"), ("error", "Error")], required=True)
    message = fields.Text(string="Detalle")
