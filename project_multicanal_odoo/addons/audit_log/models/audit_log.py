from odoo import models, fields

class AuditLog(models.Model):
    _name = "audit.log"
    _description = "Registro de accesos o eventos relevantes"

    name = fields.Char(string="Referencia", readonly=True)
    user = fields.Char(string="Usuario externo o canal")
    action_type = fields.Selection([('login', 'Login'), ('fail', 'Error'), ('other', 'Otro')], string="Tipo de evento", required=True)
    status = fields.Selection([('success', 'Éxito'), ('error', 'Error')], string="Estado", required=True)
    timestamp = fields.Datetime(string="Fecha y hora", default=fields.Datetime.now, readonly=True)
    message = fields.Text(string="Detalle")
