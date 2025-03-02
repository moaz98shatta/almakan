from . import models
from odoo import api, SUPERUSER_ID


def test_post_init_hook(env):
    env['sale.stage'].create({'code': 'draft', 'name': 'Quotation', 'stageorder': -20, 'issystem': True})
    env['sale.stage'].create({'code': 'sent', 'name': 'Quotation Sent', 'stageorder': -10, 'issystem': True})
    env['sale.stage'].create({'code': 'sale', 'name': 'Sales Order', 'stageorder': 1000, 'issystem': True})
    env['sale.stage'].create({'code': 'done', 'name': 'Locked', 'stageorder': 1100, 'issystem': True})
    env['sale.stage'].create({'code': 'cancel', 'name': 'Cancelled', 'stageorder': 1200, 'issystem': True})
    env.cr.execute(""" DROP SEQUENCE IF EXISTS seq_stage_users
    """)
    env.cr.execute(""" CREATE SEQUENCE seq_stage_users INCREMENT 1 START 1
    """)
    env.cr.execute(""" ALTER TABLE IF EXISTS res_users_sale_stage_rel
    ADD COLUMN seq integer DEFAULT nextval('seq_stage_users'::regclass)
    """)

