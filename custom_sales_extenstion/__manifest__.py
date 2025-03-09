{
    'name': 'Sales Order Extension',
    'version': '1.0',
    'summary': 'Sequential Approvals and Status',
    'description': "Parallel and sequential Approvals and Status",
    'category': 'Sales/Sales',
    'post_init_hook': 'test_post_init_hook',
    'depends': ['sale_management', 'product', 'sale'],
    'data': ['security/ir.model.access.csv', 'security/security.xml', 'views/view_actions.xml', 'views/view_menu.xml',
             'views/pricelist_item_views.xml',
             'views/view_pages.xml',
             'views/data.xml'
             ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
