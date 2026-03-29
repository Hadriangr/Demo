from django.contrib import admin
from .models import Category, Product, InventoryRecord


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'unit', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name', 'sku')


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'expected_stock', 'counted_stock', 'difference')
    list_filter = ('warehouse',)
    search_fields = ('product__name',)
