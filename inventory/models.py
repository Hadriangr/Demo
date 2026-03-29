from django.db import models
from audits.models import Warehouse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Categoría')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Producto')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=30, default='unidad', verbose_name='Unidad')
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'


class InventoryRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='records')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_records')
    expected_stock = models.IntegerField(default=0, verbose_name='Stock esperado')
    counted_stock = models.IntegerField(default=0, verbose_name='Stock contado')
    damaged_stock = models.IntegerField(default=0, verbose_name='Unidades dañadas')
    recorded_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name = 'Registro de Inventario'
        verbose_name_plural = 'Registros de Inventario'

    def __str__(self):
        return f'{self.product.name} @ {self.warehouse.name}'

    @property
    def difference(self):
        return self.counted_stock - self.expected_stock

    @property
    def shortage_units(self):
        return max(self.expected_stock - self.counted_stock, 0)
