from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'category', 'date', 'user')
    list_filter = ('category', 'date')
    search_fields = ('name', 'category')
    date_hierarchy = 'date'
