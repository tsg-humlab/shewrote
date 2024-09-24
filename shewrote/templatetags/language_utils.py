from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def past_particle(text):
    print(text)
    if not text or not isinstance(text, str):
        return text
    return text+'d' if text.endswith('e') else text+'ed'