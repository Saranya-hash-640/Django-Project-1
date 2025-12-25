from django.contrib import admin
from .models import Category, Product, Order, OrderItem

# CATEGORY
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'subcategory')
    search_fields = ('category_name',)

# PRODUCT
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')

# ORDER INLINE
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'total_price')
    extra = 0

# ORDER
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'status', 'total_amount')
    list_filter = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('order_date',)

    def total_amount(self, obj):
        return obj.total_amount
