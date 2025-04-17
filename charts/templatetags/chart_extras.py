from django import template
import calendar

register = template.Library()

@register.filter
def month_name(month_number):
    """Convert a month number (1-12) to its name."""
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, IndexError):
        return '' 