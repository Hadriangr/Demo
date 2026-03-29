from django.db import models


def alerts_counter(request):
    """Expose active alerts count for navbar badge."""
    if not request.user.is_authenticated:
        return {'alerts_count': 0}

    from inventory.models import InventoryRecord

    shortage_count = InventoryRecord.objects.filter(
        counted_stock__lt=models.F('expected_stock')
    ).count()
    damaged_count = InventoryRecord.objects.filter(damaged_stock__gt=0).count()

    return {'alerts_count': shortage_count + damaged_count}
