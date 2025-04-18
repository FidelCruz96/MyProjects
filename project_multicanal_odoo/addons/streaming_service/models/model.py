from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StreamingPlatforms(models.Model):
    _name = 'streaming.platforms'
    _description = 'Plataforma de streaming'

    name = fields.Char(string='Nombre de la plataforma')
    price_id = fields.Float(comodel_name='res.currency', string='Precio')
    profiles = fields.Integer(string='Perfiles')

    
    def subtract_profile(self):
        if self.profiles > 0:
            self.profiles -= 1
    


class StreamingSalesman(models.Model):
    _name = 'streaming.salesman'

    name = fields.Char('Nombre del vendedor')
    code = fields.Char('Codigo del vendedor')
    email = fields.Char('Correo')
    phone = fields.Char('Telefono')

    @api.model
    def create(self, vals):
        if vals.get('code', '/') == '/':
            vals['code'] = self.env['ir.sequence'].next_by_code('secuencia.codigo.cliente') or '/'
        return super(StreamingSalesman, self).create(vals)


class StreamingService(models.Model):
    _name = 'streaming.service'
    _description = 'Servicio de Streaming'
    _inherit = ['mail.thread']

    user_id = fields.Many2one('res.partner', string='Usuario')
    salesman_id = fields.Many2one('streaming.salesman', string='Vendedor') 
    platform_id = fields.Many2one('streaming.platforms', 'Plataforma')
    price_id = fields.Float('Pago',related='platform_id.price_id')
    state = fields.Selection([('active','Activo'), ('inactive','Inactivo')],string='Estado de usuario', default='active')
    payment_date = fields.Date(string='Fecha de pago realizado')
    expired_date = fields.Date(string='Fecha de vencimiento')
    start_date = fields.Date('Fecha de Inicio')
    end_date = fields.Date('Fecha de expiracion')
    
    @api.onchange('payment_date')
    def _onchange_payment_date(self):
        if self.payment_date:
            self.start_date = self.payment_date
            self.expired_date = self.payment_date + relativedelta(months=1)
            self.end_date = self.payment_date + relativedelta(months=1) + relativedelta(days=1)


    @api.onchange('end_date','payment_date')
    def _compute_state(self):
        today = fields.Date.today()
        for service in self:
            state = []
            if service.expired_date and service.expired_date < today:
                state = 'inactive'
            else:
                state = 'active'
            service.state = state
            
            

    @api.constrains('user_id', 'platform_id')
    def _check_platform_assignment(self):
        for service in self:
            if service.platform_id and service.user_id:
                existing_service = self.search([
                    ('id', '!=', service.id),
                    ('platform_id', '=', service.platform_id.id),
                    ('user_id', '=', service.user_id.id)
                ])
                if existing_service:
                    raise ValidationError('El usuario ya tiene asignada esta plataforma.')


    @api.constrains('user_id')
    def _check_state_user(self):

        for service in self:
            if service.user_id:
                inactive_user = self.search([
                    ('id', '!=', service.id),
                    ('user_id', '=', service.user_id.id),
                    ('state', '=', 'inactive')
                ])
                if inactive_user:
                    raise ValidationError('El usuario está inactivo en uno de sus perfiles')
    
    #En los campos relacionados se puede aplicar los metodos que se hayan escrito en su clase
    @api.onchange('platform_id')
    def _onchange_platform_id(self):
        if self.platform_id:
            self.platform_id.subtract_profile()


    @api.constrains('platform_id')
    def _check_profile_availability(self):
        for service in self:
            if service.platform_id and service.platform_id.profiles <= 0:
                raise ValidationError("La plataforma no tiene perfiles disponibles.")
