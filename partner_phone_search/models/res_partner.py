import re

from odoo import api, models
from odoo.fields import Domain

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
            domain = Domain(domain) | self._search_phone_mobile_search(operator, number)
            if number.startswith('00'):
                # phone_validation reads a leading 00 as an international prefix
                # only. It ignores the bracket, which makes this a search on a
                # part of the number: ...123 00 45 is found by 0045.
                domain |= self._search_phone_mobile_search(operator, f'({number}')
        return domain

    @api.model
    @api.readonly
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):
        results = super().web_name_search(
            name, specification, domain=domain, operator=operator, limit=limit,
        )
        if not self._is_phone_search_term(operator, name):
            return results
        # The number only goes on the label of the suggestion, which the
        # autocomplete reads first (web/.../relational_utils.js,
        # buildRecordSuggestion). display_name is what the many2one keeps once
        # a suggestion is picked, so it must stay the plain name.
        phones = {
            partner.id: partner.phone
            for partner in self.browse([result['id'] for result in results])
        }
        for result in results:
            phone = phones.get(result['id'])
            label = result.get('__formatted_display_name') or result.get('display_name')
            if phone and label:
                result['__formatted_display_name'] = f"{label}  —  {phone}"
        return results
