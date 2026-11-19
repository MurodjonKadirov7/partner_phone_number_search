import re

from odoo import api, models
from odoo.osv import expression

# What a typed phone number looks like: digits and phone punctuation only.
_PHONE_INPUT_RE = re.compile(r'^[\d\s+().\-/]+$')
_NON_DIGITS_RE = re.compile(r'\D')
# \d also matches the digits of other scripts (Arabic-Indic, full-width...).
_DIGIT_RE = re.compile(r'\d')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _is_phone_search_term(self, operator, value):
        """Whether the searched value can be used as a phone number search."""
        if not isinstance(value, str):
            return False
        # Not =like / =ilike: they match a whole value, phone_validation would
        # turn them into a search on a part of the number.
        if operator not in ('like', 'ilike'):
            return False
        value = value.strip()
        if not value or not _PHONE_INPUT_RE.match(value):
            return False
        digits = _NON_DIGITS_RE.sub('', value)
        return len(digits) >= (self._phone_search_min_length or 3)

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if self._is_phone_search_term(operator, value):
            # OR the normalized search of phone_validation with the standard
            # result: the search on name, email, reference... stays as it is.
            number = _DIGIT_RE.sub(lambda digit: str(int(digit[0])), value).strip()
            # Odoo 18: odoo.fields.Domain yo'q — expression.OR (odoo/osv/expression.py:308)
            domains = [domain, self._search_phone_mobile_search(operator, number)]
            if number.startswith('00'):
                # phone_validation reads a leading 00 as an international prefix
                # only. It ignores the bracket, which makes this a search on a
                # part of the number: ...123 00 45 is found by 0045.
                domains.append(self._search_phone_mobile_search(operator, f'({number}'))
            domain = expression.OR(domains)
        return domain

    @api.model
    @api.readonly
    def phone_name_search(self, name='', args=None, operator='ilike', limit=100):
        """name_search + the suggestion label with the phone number.

        Odoo 18 has no web_name_search: the autocomplete builds both the
        suggestion label and the value kept once picked from the name_search
        pair (web/static/src/views/fields/relational_utils.js:314-326). This
        method returns (id, display_name, label): our JS patch shows the label
        and keeps display_name, so the picked value stays the plain name.
        label is False when there is nothing to add.
        """
        results = self.name_search(name, args=args, operator=operator, limit=limit)
        if not self._is_phone_search_term(operator, name):
            return [(partner_id, display_name, False) for partner_id, display_name in results]
        phones = {
            partner.id: partner.phone
            for partner in self.browse([partner_id for partner_id, _name in results])
        }
        labelled = []
        for partner_id, display_name in results:
            phone = phones.get(partner_id)
            label = (display_name or '').split('\n')[0]
            labelled.append((partner_id, display_name, f"{label}  —  {phone}" if phone and label else False))
        return labelled
