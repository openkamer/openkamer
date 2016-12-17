from django import template

from django.utils.text import slugify

register = template.Library()


@register.assignment_tag
def get_besluitenlijst_item_anchor(item):
    return slugify(item.title)
