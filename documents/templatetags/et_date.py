"""
Template tag/filter: Ethiopian calendar date display.
Usage in templates:
  {% load et_date %}
  {{ doc.created_at|et_date }}        -> "5 መስከረም 2017 ዓ.ም"
  {{ doc.created_at|et_date_short }}  -> "5/1/2017"
"""
from django import template
from documents.utils import to_ethiopian

register = template.Library()


@register.filter
def et_date(value):
    """Return full Ethiopian date string."""
    result = to_ethiopian(value)
    return result['full'] if result else ''


@register.filter
def et_date_short(value):
    """Return short Ethiopian date string d/m/yyyy."""
    result = to_ethiopian(value)
    return result['short'] if result else ''


@register.filter
def et_year(value):
    """Return Ethiopian year only."""
    result = to_ethiopian(value)
    return result['year'] if result else ''
