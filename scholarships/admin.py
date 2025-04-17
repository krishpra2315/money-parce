from django.contrib import admin
from .models import Scholarship, CollegeDebt

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'user', 'date_added')
    list_filter = ('date_added',)
    search_fields = ('name', 'user__email')

@admin.register(CollegeDebt)
class CollegeDebtAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_amount', 'scholarship_coverage_percentage')
    search_fields = ('user__email',)
