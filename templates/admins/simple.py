from django import template

register = template.Library()

@register.simple_tag
def getitem(dictionary, key):
    try:
        return dictionary.get(key, 0)
    except:
        return 0