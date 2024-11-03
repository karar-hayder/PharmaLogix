from django import template

register = template.Library()

@register.filter(name='has_perm')
def has_perm(user, perm_name):
    """Check if the user has a specific permission."""
    return user.has_perm(perm_name)