from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard:index')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('core:login')


def alerts_view(request):
    from inventory.models import InventoryRecord

    shortage_records = (
        InventoryRecord.objects
        .filter(counted_stock__lt=models.F('expected_stock'))
        .select_related('product', 'warehouse', 'product__category')
        .order_by('warehouse__name', 'product__name')
    )
    damaged_records = (
        InventoryRecord.objects
        .filter(damaged_stock__gt=0)
        .select_related('product', 'warehouse', 'product__category')
        .order_by('-damaged_stock', 'warehouse__name')
    )

    context = {
        'shortage_records': shortage_records,
        'damaged_records': damaged_records,
    }
    return render(request, 'alerts.html', context)
