{
    'name': 'Purchase Request Management',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Manage purchase requests from departments',
    'depends': ['purchase', 'hr', 'product'],
    'data': [
        'security/purchase_request_security.xml',
        'security/ir.model.access.csv',
        'data/purchase_request_sequence.xml',
        'views/purchase_request_line_view.xml',
        'views/purchase_request_view.xml',
        'views/purchase_request_menu.xml',

    ],
    'installable': True,
    'application': True,
}
