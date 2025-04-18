from odoo import models, fields, api
from datetime import datetime
from odoo.http import request
import requests

class UserRiskHistory(models.Model):
    _name = 'user.risk.history'
    _description = 'Historial de Riesgo de Usuario'

    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now, required=True)
    description = fields.Text(string='Descripción del Riesgo')
    severity = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], string='Severidad', required=True)
    login_ip = fields.Char(string='IP de Inicio de Sesión')
    login_location = fields.Char(string='Ubicación de Inicio de Sesión')

    @api.model
    def create(self, vals):
        user = self.env['res.users'].browse(vals['user_id'])
        vals['login_ip'] = user.last_login_ip
        vals['login_location'] = user.last_login_location
        return super(UserRiskHistory, self).create(vals)



class ResUsers(models.Model):
    _inherit = 'res.users'

    login_count = fields.Integer(string='Número de Inicios de Sesión', default=0)
    risk_level = fields.Selection([
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico')
    ], string='Nivel de Riesgo', compute='_compute_risk_level', store=True)
    last_login_date = fields.Datetime(string='Última Actividad')
    last_login_ip = fields.Char(string='Última IP')
    last_login_location = fields.Char(string='Última Ubicación')
    risk_history_ids = fields.One2many('user.risk.history', 'user_id', string='Historial de Riesgo')

    def _compute_risk_level(self):
        for user in self:
            # Lógica para determinar el nivel de riesgo basado en actividades recientes
            if user.login_count > 100 and any(risk.severity == 'critical' for risk in user.risk_history_ids):
                user.risk_level = 'critical'
            elif user.login_count > 50:
                user.risk_level = 'high'
            elif user.login_count > 20:
                user.risk_level = 'medium'
            else:
                user.risk_level = 'low'

    @api.model
    def _auth_user(self, login, password):
        user = super(ResUsers, self)._auth_user(login, password)
        if user:
            ip_address = request.httprequest.remote_addr
            user.last_login_ip = ip_address
            user.last_login_location = self._get_location_from_ip(ip_address)
            user.last_login_date = fields.Datetime.now()
            user.login_count += 1
        return user

    def _get_location_from_ip(self, ip):
        # Ejemplo usando un servicio de geolocalización por IP
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}')
            data = response.json()
            return f"{data.get('city')}, {data.get('country')}"
        except Exception as e:
            return "Ubicación Desconocida"