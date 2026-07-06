from django.contrib import admin

from.models import *


# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_editable = ['status']

admin.site.register(Product)
admin.site.register(Category)

