from django import template
from django.utils.safestring import mark_safe

from game.ui_translations import ui_text


register = template.Library()


@register.simple_tag
def ui(value):
    # The catalog is maintained in source control and contains plain UI text.
    # Marking it safe also keeps apostrophes usable inside inline JavaScript.
    return mark_safe(ui_text(value))
