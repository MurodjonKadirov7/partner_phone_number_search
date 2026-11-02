from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPartnerPhoneSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env['res.partner']
        cls.formatted = Partner.create({'name': 'Ali Valiyev', 'phone': '+998 90 123 45 67'})
        cls.brackets = Partner.create({'name': 'Vali Aliyev', 'phone': '(90) 765-43-21'})
        cls.no_phone = Partner.create({'name': 'Zero Phone', 'ref': '901234567'})
        cls.numbered = Partner.create({'name': 'Warehouse 555'})

    def _names(self, term, operator='ilike'):
        return self.env['res.partner'].browse(
            [pair[0] for pair in self.env['res.partner'].name_search(term, operator=operator, limit=100)])

    def _web_search(self, term):
        return self.env['res.partner'].web_name_search(term, {'display_name': {}}, limit=100)

    def test_number_found_without_its_formatting(self):
        for term in ('901234567', '90 123 45 67', '(90) 123-45-67', '90.123.45.67', '123 45'):
            self.assertIn(self.formatted, self._names(term), term)
        self.assertIn(self.brackets, self._names('907654321'))

    def test_international_prefixes(self):
        for term in ('+998901234567', '+998 90 123', '00998901234567'):
            self.assertIn(self.formatted, self._names(term), term)

    def test_standard_search_still_works(self):
        self.assertIn(self.formatted, self._names('Ali Val'))
        # digits in a name or a reference: not lost because of the phone search
        self.assertIn(self.numbered, self._names('555'))
        self.assertIn(self.no_phone, self._names('901234567'))

    def test_what_is_not_a_phone_search(self):
        partner = self.env['res.partner']
        self.assertFalse(partner._is_phone_search_term('ilike', 'Ali 90'))
        self.assertFalse(partner._is_phone_search_term('ilike', '12'), 'too short')
        self.assertFalse(partner._is_phone_search_term('ilike', '+ - ( )'), 'no digits')
        self.assertFalse(partner._is_phone_search_term('ilike', '   '))
        self.assertFalse(partner._is_phone_search_term('ilike', False))
        self.assertFalse(partner._is_phone_search_term('not ilike', '901234567'))
        self.assertFalse(partner._is_phone_search_term('=', '901234567'))
        self.assertTrue(partner._is_phone_search_term('ilike', ' +998 90 '))

    def test_pattern_operators_keep_their_meaning(self):
        # =ilike and =like match the whole value, a phone search matches a part
        partner = self.env['res.partner']
        self.assertFalse(partner._is_phone_search_term('=ilike', '901234567'))
        self.assertFalse(partner._is_phone_search_term('=like', '901234567'))
        for operator in ('=ilike', '=like'):
            self.assertNotIn(self.formatted, self._names('901234567', operator=operator), operator)
            self.assertIn(self.no_phone, self._names('901234567', operator=operator), 'the reference matches')

    def test_digits_of_other_scripts(self):
        for term in ('٩٠١٢٣٤٥٦٧', '۹۰۱۲۳۴۵۶۷', '９０１２３４５６７', '+٩٩٨ ٩٠ ١٢٣', '٠٠٩٩٨٩٠١٢٣٤٥٦٧'):
            self.assertIn(self.formatted, self._names(term), term)
        self.assertTrue(self._web_search('٩٠١٢٣٤٥٦٧'))

    def test_part_of_a_number_starting_with_00(self):
        # phone_validation reads a leading 00 as an international prefix only
        partner = self.env['res.partner'].create({'name': 'Zeros', 'phone': '+998 90 123 00 45'})
        self.assertIn(partner, self._names('0045'))
        self.assertIn(partner, self._names('00 45'))
        self.assertIn(partner, self._names('00998 90 123'), 'still an international prefix')

    def test_hostile_terms(self):
        for term in ('%%%', '___', '90%', '9_0', '1' * 100000, '1 ' * 50000, '٠' * 1000, "1'; --", '123\\'):
            self._names(term)
            self._web_search(term)
        self.assertNotIn(self.formatted, self._names('9_1234567'), 'not a wildcard')

    def test_web_name_search_stays_readonly(self):
        # web/controllers/dataset.py reads the attribute on the final override
        self.assertTrue(getattr(self.env['res.partner'].web_name_search, '_readonly', False))

    def test_short_or_empty_terms_do_not_raise(self):
        # phone_validation raises on less than 3 characters: never reached here
        for term in ('', ' ', '1', '12', '+', '()'):
            self._names(term)
            self._web_search(term)

    def test_negative_operator_excludes_nothing_extra(self):
        found = self.env['res.partner'].search([('display_name', 'not ilike', 'Ali Valiyev')])
        self.assertNotIn(self.formatted, found)
        self.assertIn(self.brackets, found)

    def test_display_name_search_on_a_relation(self):
        # The customer filter of a list goes through the same search
        child = self.env['res.partner'].create({'name': 'Child', 'parent_id': self.formatted.id})
        found = self.env['res.partner'].search([('parent_id', 'ilike', '901234567')])
        self.assertIn(child, found)

    def test_suggestion_label_shows_the_number(self):
        results = {res['id']: res for res in self._web_search('901234567')}
        label = results[self.formatted.id]['__formatted_display_name']
        self.assertIn('Ali Valiyev', label)
        self.assertIn(self.formatted.phone, label)

    def test_picked_value_keeps_the_plain_name(self):
        # display_name is what the many2one shows once a suggestion is picked
        results = {res['id']: res for res in self._web_search('901234567')}
        self.assertEqual(results[self.formatted.id]['display_name'], self.formatted.display_name)
        self.assertNotIn(self.formatted.phone, self.formatted.display_name)

    def test_partner_without_phone_keeps_its_label(self):
        results = {res['id']: res for res in self._web_search('901234567')}
        self.assertEqual(results[self.no_phone.id]['__formatted_display_name'], 'Zero Phone')

    def test_name_search_label_untouched(self):
        results = {res['id']: res for res in self._web_search('Ali Valiyev')}
        self.assertNotIn('+998', results[self.formatted.id]['__formatted_display_name'])

    def test_wider_specification(self):
        results = self.env['res.partner'].web_name_search(
            '901234567', {'display_name': {}, 'email': {}}, limit=100)
        result = next(res for res in results if res['id'] == self.formatted.id)
        self.assertEqual(result['display_name'], self.formatted.display_name)
        self.assertIn(self.formatted.phone, result['__formatted_display_name'])

    def test_record_rules_still_apply(self):
        other = self.env['res.company'].create({'name': 'Other company'})
        hidden = self.env['res.partner'].create({
            'name': 'Hidden', 'phone': '+998 91 000 11 22', 'company_id': other.id,
        })
        user = self.env['res.users'].create({
            'name': 'Sales user', 'login': 'phone_search_user',
            'group_ids': [(6, 0, self.env.ref('base.group_user').ids)],
        })
        self.assertIn(hidden, self._names('910001122'))
        found = self.env['res.partner'].with_user(user).name_search('910001122')
        self.assertNotIn(hidden.id, [pair[0] for pair in found])
