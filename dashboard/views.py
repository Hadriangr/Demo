import json
import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone


MONTHS_ES_ABBR = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
]
MONTHS_ES_FULL = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


def month_label_es(dt_value):
    if not dt_value:
        return ''
    return f"{MONTHS_ES_ABBR[dt_value.month - 1]} {dt_value.year}"


def month_label_es_full(dt_value):
    if not dt_value:
        return ''
    return f"{MONTHS_ES_FULL[dt_value.month - 1]} {dt_value.year}"


def month_value(dt_value):
    return dt_value.strftime('%Y-%m')


def parse_month_value(month_raw, fallback_month):
    if not month_raw:
        return fallback_month
    try:
        parsed = datetime.datetime.strptime(month_raw, '%Y-%m').date()
        return parsed.replace(day=1)
    except ValueError:
        return fallback_month


@login_required
def index(request):
    from audits.models import Audit
    from inventory.models import InventoryRecord

    today = timezone.now().date()

    available_months = [
        m for m in (
            InventoryRecord.objects
            .annotate(month=TruncMonth('recorded_at'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('-month')
        ) if m
    ]

    default_month = available_months[0].date().replace(day=1) if available_months else today.replace(day=1)
    selected_month = parse_month_value(request.GET.get('month'), default_month)

    if selected_month.month == 12:
        selected_month_end = selected_month.replace(year=selected_month.year + 1, month=1, day=1)
    else:
        selected_month_end = selected_month.replace(month=selected_month.month + 1, day=1)

    month_filter = {
        'recorded_at__date__gte': selected_month,
        'recorded_at__date__lt': selected_month_end,
    }

    total_audits = Audit.objects.count()
    pending_audits = Audit.objects.filter(status__in=['pending', 'in_progress']).count()

    shortage_count = InventoryRecord.objects.filter(
        counted_stock__lt=models.F('expected_stock'),
        **month_filter,
    ).count()
    damaged_count = InventoryRecord.objects.filter(damaged_stock__gt=0, **month_filter).count()
    inventory_alerts = shortage_count + damaged_count

    completed = Audit.objects.filter(status='completed')
    if completed.exists():
        avg_compliance = round(sum(a.compliance_pct for a in completed) / completed.count(), 1)
    else:
        avg_compliance = 0

    # Chart: audits per month (last 6 months)
    six_months_ago = today.replace(day=1)
    monthly = (
        Audit.objects
        .filter(created_at__date__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    chart_months = [month_label_es(item['month']) for item in monthly]
    chart_counts = [item['count'] for item in monthly]

    # Chart: audits per warehouse
    per_warehouse = (
        Audit.objects
        .values('warehouse__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    wh_labels = [item['warehouse__name'] for item in per_warehouse]
    wh_counts = [item['count'] for item in per_warehouse]

    # Chart: damaged units per month (last 6 months)
    damaged_monthly = (
        InventoryRecord.objects
        .annotate(month=TruncMonth('recorded_at'))
        .values('month')
        .annotate(total=Sum('damaged_stock'))
        .order_by('month')
    )
    damaged_month_labels = [month_label_es(item['month']) for item in damaged_monthly if item['month']]
    damaged_month_values = [int(item['total'] or 0) for item in damaged_monthly if item['month']]

    damaged_products_selected_month = (
        InventoryRecord.objects
        .filter(damaged_stock__gt=0, **month_filter)
        .values('product__name')
        .annotate(total_damaged=Sum('damaged_stock'))
        .order_by('-total_damaged', 'product__name')
    )

    # Chart: products that reached out-of-stock month by month
    out_of_stock_monthly = (
        InventoryRecord.objects
        .filter(counted_stock=0)
        .annotate(month=TruncMonth('recorded_at'))
        .values('month')
        .annotate(products=Count('product', distinct=True))
        .order_by('month')
    )

    out_stock_month_labels = [month_label_es(item['month']) for item in out_of_stock_monthly if item['month']]
    out_stock_month_values = [int(item['products'] or 0) for item in out_of_stock_monthly if item['month']]

    out_stock_products_selected_month = (
        InventoryRecord.objects
        .filter(counted_stock=0, **month_filter)
        .values('product__name')
        .annotate(warehouses=Count('warehouse', distinct=True))
        .order_by('-warehouses', 'product__name')
    )

    recent_audits = Audit.objects.select_related('warehouse', 'auditor')[:5]

    month_options = [
        {
            'value': month_value(m),
            'label': month_label_es_full(m),
        }
        for m in available_months
    ]

    context = {
        'total_audits': total_audits,
        'pending_audits': pending_audits,
        'inventory_alerts': inventory_alerts,
        'shortage_count': shortage_count,
        'damaged_count': damaged_count,
        'avg_compliance': avg_compliance,
        'chart_months': json.dumps(chart_months),
        'chart_counts': json.dumps(chart_counts),
        'wh_labels': json.dumps(wh_labels),
        'wh_counts': json.dumps(wh_counts),
        'damaged_month_labels': json.dumps(damaged_month_labels),
        'damaged_month_values': json.dumps(damaged_month_values),
        'out_stock_month_labels': json.dumps(out_stock_month_labels),
        'out_stock_month_values': json.dumps(out_stock_month_values),
        'month_label': month_label_es_full(selected_month),
        'selected_month_value': month_value(selected_month),
        'month_options': month_options,
        'damaged_products_selected_month': damaged_products_selected_month,
        'out_stock_products_selected_month': out_stock_products_selected_month,
        'recent_audits': recent_audits,
    }
    return render(request, 'dashboard.html', context)
