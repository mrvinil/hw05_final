from django import template

register = template.Library()
ugli = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})
