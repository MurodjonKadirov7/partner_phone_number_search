# Copyright todoo.uz. License OPL-1 (Odoo Proprietary License v1.0).
{
    'name': 'Partner Phone Search | Find Customers by Phone Number',
    'version': '18.0.1.1.1',
    'category': 'Sales/Sales',
    'summary': 'Type a phone number in any customer or contact field and find the '
               'partner, whatever the format: spaces, brackets, dashes, +, 00',
    'description': """
Partner Phone Search
====================
Typing a phone number in a customer field (sales orders, quotations, invoices,
any partner field) finds the partner. The number is matched without its
formatting: a contact saved as +998 90 123 45 67 is found by 901234567.
The number shows next to the name in the suggestions. The usual search on
name, email and reference keeps working.
""",
    'author': 'todoo.uz',
    'website': 'https://todoo.uz',
    'support': 'info@todoo.uz',
    'license': 'OPL-1',
    'images': ['static/description/banner.png'],
    'depends': ['phone_validation'],
    'assets': {
        'web.assets_backend': [
            'partner_phone_number_search/static/src/js/phone_autocomplete.js',
        ],
    },
    'installable': True,
    'application': False,
}
