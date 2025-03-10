from odoo import api, fields, models, tools, _
from datetime import date, datetime, timedelta
from odoo.exceptions import ValidationError

from passlib.ext.django.utils import ProxyProperty
from pyasn1.debug import Printer


class SaleExt(models.Model):
    _inherit = 'sale.order'

    saletype = fields.Many2one('sale.stage.type', string='Order type', compute='_calc_stage',
                               inverse='_get_type', tracking=3,
                               store=True)
    state = fields.Selection(selection=lambda self: self.get_stages(), string='Status',
                             readonly=True, copy=False, index=True, tracking=3, default='draft'
                             )
    showpending = fields.Boolean(string='pending status', compute='_show_pending_status', depends=['state'],
                                 store=False)
    userisadmin = fields.Boolean(compute='_check_admin', default=True)

    done_state = fields.Boolean( default=False)
    confirm_on_create = fields.Boolean(default=False)
    is_hide = fields.Boolean(default=False)



    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        # if self.state not in {'draft', 'sent'}:
        #     return _("Some orders are not in a state requiring confirmation.")
        if any(
                not line.display_type
                and not line.is_downpayment
                and not line.product_id
                for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent'} or int

    @api.depends('amount_total', 'pricelist_id')
    def _calc_stage(self):
        tot = 0
        currid = 0

        for rec in self:
            tot += rec.amount_total
            price_id = rec.pricelist_id.id

        ret_type = self.env['sale.stage.type'].search([('pricelist', '=', price_id),
                                                       ], limit=1)
        print("rrrreeet typeee----", ret_type)

        self.saletype = ret_type

    def _check_admin(self):
        ret = False
        if self.state in ('draft', 'sent'):
            ret = True
        elif self.state in ('sale', 'done'):
            ret = False
        else:
            user0 = self.env['res.users'].browse(self.env.uid)
            ret = user0.has_group('custom_sales_extenstion.custom_sales_stage_type')
        self.userisadmin = ret

    def _get_type(self):
        ret = False
        if self.state in ('draft', 'sent'):
            pass
        else:
            user0 = self.env['res.users'].browse(self.env.uid)
            ret = user0.has_group('custom_sales_extenstion.custom_sales_stage_type')
            if ret:
                self._change_type()
            else:
                raise ValidationError("A hacking is attempted")

    def _change_type(self):
        self.env['sale.order.pending'].search([('user', '=', self.env.uid)
                                                  , ('saleorder', '=', self.id)]
                                              ).unlink()
        for act in self.activity_ids:
            if act.activity_type_id.id == 4 and act.res_id == self.id:
                act.action_feedback('Request is changed')
        self.state = 'sent'
        rec_id = self.env['ir.model'].sudo().search([('model', '=', 'sale.order')], limit=1)
        if self.user_id:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': 4,
                'date_deadline': date.today(),
                'summary': 'Sale type stage has changed',
                'user_id': self.user_id.id,
                'res_model_id': rec_id.id,
                'res_id': self.id
            })
        self.process_stages()

    def get_stages(self):

        lst = []
        recset = self.env['sale.stage'].search([], order='stageorder')
        for stg in recset:
            lst.append((stg.code, stg.name))
        return lst

    def dynamic_selection(self):
        select = [
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled'),
        ]
        return select

    def action_confirm(self):
        if self.saletype:
            if self.state in ('draft', 'sent') and self.done_state == False:
                price_id = self.pricelist_id.id
                product_pricelist = self.env['product.pricelist'].search([('id', '=', price_id)], limit=1)
                if product_pricelist:
                    for line in self.order_line:
                        if line:
                            itemexist = self.env['product.pricelist.item'].search([
                                ('product_tmpl_id', '=', line.product_template_id.id),
                                ('pricelist_id', '=', product_pricelist.id)
                            ], limit=1)

                            if itemexist and itemexist.min_price > line.price_unit or (line.price_unit * line.discount) / 100 < itemexist.min_price :
                                newlist = sorted(self.saletype.stages, key=lambda x: x.stageorder)
                                self.state = newlist[0].code
                                self.process_stages()
                            else:
                                self.is_hide = True
                                super(SaleExt, self).action_confirm()
            elif (self.confirm_on_create and self.done_state):
                self.is_hide = True
                super(SaleExt, self).action_confirm()
            elif self.confirm_on_create:
                True
            else:
                self.is_hide = True
                super(SaleExt, self).action_confirm()



        else:
            self.is_hide = True
            super(SaleExt, self).action_confirm()

    def _show_pending_status(self):

        ret = False
        if self.saletype:

            if self.state in self.saletype.get_stage_list():
                if self.env['sale.order.pending'].search_count([('user', '=', self.env.uid)
                                                                   , ('state', '=', self.state)
                                                                   , ('saleorder', '=', self.id)
                                                                   , ('status', '=', 'waiting')]):
                    ret = True

        self.showpending = ret

    def action_approve(self):
        rec = self.env['sale.order.pending'].search([
            ('user', '=', self.env.uid)
            , ('state', '=', self.state)
            , ('saleorder', '=', self.id)
            , ('status', '=', 'waiting')
        ], limit=1)
        if rec:
            oldstate = self.state
            rec[0].update({'status': 'approve'})
            for act in self.activity_ids:
                if act.activity_type_id.id == 4 and act.res_id == self.id and act.user_id.id == self.env.uid:
                    act.action_feedback(feedback='Request is approved')
            self.check_stage()
            current_stage = self.env['sale.stage'].sudo().search([('code', '=', self.state)], limit=1)
            self.done_state = True



    def action_decline(self):

        rec = self.env['sale.order.pending'].search([
            ('user', '=', self.env.uid)
            , ('state', '=', self.state)
            , ('saleorder', '=', self.id)
            , ('status', '=', 'waiting')
        ], limit=1)
        if rec:
            rec[0].update({'status': 'decline'})
            self.state = 'cancel'
            super(SaleExt, self).action_cancel()

    def check_stage(self):

        # lst_users=list(filter(lambda s:s.code==self.state,self.saletype.stages))
        count_approve = self.env['sale.order.pending'].search_count([('state', '=', self.state)
                                                                        , ('saleorder', '=', self.id)
                                                                        , ('status', '=', 'approve')])
        current_stage = self.env['sale.stage'].sudo().search([('code', '=', self.state)], limit=1)
        newlist = sorted(self.saletype.stages, key=lambda x: x.stageorder)

        if len(current_stage.stageusers) >= count_approve:
            if current_stage.code == newlist[len(newlist) - 1].code:
                super(SaleExt, self).action_cancel()
                super(SaleExt, self).action_draft()
                self.state= 'draft'
                # super(SaleExt, self).action_confirm()
            else:
                for x in range(0, len(newlist) - 1):
                    if newlist[x].code == current_stage.code:
                        self.state = newlist[x + 1].code
                        self.process_stages()
                        break

    def process_stages(self):
        current_stage = self.env['sale.stage'].sudo().search([('code', '=', self.state)], limit=1)
        uorder = 0
        rec_id = self.env['ir.model'].sudo().search([('model', '=', 'sale.order')], limit=1)
        qquery = " select seq,res_users_id  from res_users_sale_stage_rel  where sale_stage_id=" + str(
            current_stage.id) + " order by seq"
        self.env.cr.execute(qquery)
        stage_users = self.env.cr.fetchall()
        for user in stage_users:
            if current_stage.approvetype == 'sequence':
                self.env['sale.order.pending'].create({
                    'user': user[1],
                    'saleorder': self.id,
                    'state': self.state,
                    'status': 'waiting',
                    'userorder': uorder
                })
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'date_deadline': date.today(),
                    'summary': 'Request to approve',
                    'user_id': user[1],
                    'res_model_id': rec_id.id,
                    'res_id': self.id
                })

    def _check_pricing_conditions(self):
        if self.saletype:
            if self.state in ('draft', 'sent') and self.done_state == False:
                price_id = self.pricelist_id.id
                product_pricelist = self.env['product.pricelist'].search([('id', '=', price_id)], limit=1)
                if product_pricelist:
                    for line in self.order_line:
                        if line:
                            itemexist = self.env['product.pricelist.item'].search([
                                ('product_tmpl_id', '=', line.product_template_id.id),
                                ('pricelist_id', '=', product_pricelist.id)
                            ], limit=1)

                            if itemexist and itemexist.min_price > line.price_unit or ((line.price_unit * line.discount) / 100 < itemexist.min_price if line.discount else False):
                                newlist = sorted(self.saletype.stages, key=lambda x: x.stageorder)
                                self.state = newlist[0].code
                                self.process_stages()
                                self.confirm_on_create = True
            else:
                self.action_confirm()



    @api.model
    def create(self, vals):
        sale_order = super(SaleExt, self).create(vals)
        sale_order._check_pricing_conditions()
        return sale_order


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_hide = fields.Boolean(string="Hide Price",related='order_id.is_hide', default=False)





