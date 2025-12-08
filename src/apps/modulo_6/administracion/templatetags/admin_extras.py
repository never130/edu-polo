from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave dinámica.
    Uso: {{ diccionario|get_item:clave }}
    """
    return dictionary.get(key)
