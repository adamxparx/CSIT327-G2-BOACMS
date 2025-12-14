from django import template
from ..models import BarangayStaff
register = template.Library()

@register.filter
def get_staff_name(user):
    """
    Get the staff name from the BarangayStaff related object
    """
    try:
        # Try to get the related BarangayStaff object
        staff = BarangayStaff.objects.get(user=user)
        if staff.first_name and staff.last_name:
            if staff.middle_name:
                return f"{staff.first_name} {staff.middle_name} {staff.last_name}"
            else:
                return f"{staff.first_name} {staff.last_name}"
    except BarangayStaff.DoesNotExist:
        pass
    except Exception:
        pass
    return "Barangay Staff"