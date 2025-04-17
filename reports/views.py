from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, ExtractYear
from transactions.models import Transaction
from budgets.models import MonthlyBudget, BudgetCategory
from goals.models import Goal
from django.http import HttpResponse
import datetime
import calendar
import csv

# Create your views here.

@login_required
def yearly_report(request):
    """
    Generate a yearly financial report showing:
    - Total transactions
    - Total savings contributed (goals)
    - Current budgets
    """
    # Get the year from the request, default to the current year
    year = request.GET.get('year')
    try:
        year = int(year) if year else datetime.datetime.now().year
    except ValueError:
        year = datetime.datetime.now().year
    
    # Get all years with transaction data for the dropdown
    years_with_data = Transaction.objects.filter(user=request.user) \
        .dates('date', 'year') \
        .values_list('date__year', flat=True) \
        .distinct() \
        .order_by('-date__year')
    
    # If no data or year not in data years, default to current year
    if not years_with_data:
        years_with_data = [datetime.datetime.now().year]
    if year not in years_with_data:
        year = datetime.datetime.now().year
    
    # Get transactions for the selected year
    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=year
    )
    
    # Get total transactions amount for the year
    total_transactions_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get transaction count per month
    monthly_transaction_counts = []
    monthly_transaction_amounts = []
    
    for month in range(1, 13):
        # Get transaction count for the month
        month_transactions = transactions.filter(date__month=month)
        count = month_transactions.count()
        amount = month_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_transaction_counts.append({
            'month': calendar.month_name[month],
            'count': count,
        })
        
        monthly_transaction_amounts.append({
            'month': calendar.month_name[month],
            'amount': amount,
        })
    
    # Get category breakdowns for the year
    category_breakdown = transactions.values('category') \
        .annotate(total=Sum('amount'), count=Count('id')) \
        .order_by('-total')
    
    # Get goals (savings) information
    goals = Goal.objects.filter(user=request.user)
    
    # Calculate total savings for the year
    # Note: This is an approximation as we don't have the actual contribution dates
    total_savings = goals.aggregate(total=Sum('current_amount'))['total'] or 0
    
    # Get budget information for the current year
    # Start by getting all budget categories for this user
    budget_categories = BudgetCategory.objects.filter(user=request.user)
    
    # Get the current month's budgets
    current_month = datetime.datetime.now().replace(day=1)
    current_budgets = MonthlyBudget.objects.filter(
        user=request.user,
        month__year=year
    ).order_by('month')
    
    # Group budgets by month
    monthly_budgets = {}
    for budget in current_budgets:
        month_key = budget.month.strftime('%B %Y')
        if month_key not in monthly_budgets:
            monthly_budgets[month_key] = []
        
        monthly_budgets[month_key].append({
            'category': budget.category.get_name_display(),
            'amount': budget.amount,
        })
    
    # Organize context data
    context = {
        'year': year,
        'years_with_data': years_with_data,
        'total_transactions': transactions.count(),
        'total_transactions_amount': total_transactions_amount,
        'monthly_transaction_counts': monthly_transaction_counts,
        'monthly_transaction_amounts': monthly_transaction_amounts,
        'category_breakdown': category_breakdown,
        'goals': goals,
        'total_savings': total_savings,
        'monthly_budgets': monthly_budgets,
    }
    
    return render(request, 'reports/yearly_report.html', context)

@login_required
def download_report_csv(request, year=None):
    """
    Generate and download a CSV report of the yearly financial data
    """
    # Get the year from the request or URL parameter, default to the current year
    if year is None:
        year = request.GET.get('year')
        try:
            year = int(year) if year else datetime.datetime.now().year
        except ValueError:
            year = datetime.datetime.now().year
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    filename = f'financial_report_{year}_{request.user.name.replace(" ", "_")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the CSV writer
    writer = csv.writer(response)
    
    # Add report title and date
    writer.writerow([f'Financial Report - {year}'])
    writer.writerow([f'Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([f'User: {request.user.name}'])
    writer.writerow([])  # Empty row for spacing
    
    # Get transactions for the selected year
    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=year
    )
    
    # Get totals
    total_transactions = transactions.count()
    total_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Add summary section
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Transactions', total_transactions])
    writer.writerow(['Total Amount', f'${total_amount:.2f}'])
    
    # Get goals (savings) information
    goals = Goal.objects.filter(user=request.user)
    total_savings = goals.aggregate(total=Sum('current_amount'))['total'] or 0
    writer.writerow(['Total Savings', f'${total_savings:.2f}'])
    writer.writerow(['Savings Goals Count', goals.count()])
    writer.writerow([])  # Empty row for spacing
    
    # Monthly transaction breakdown
    writer.writerow(['MONTHLY TRANSACTIONS'])
    writer.writerow(['Month', 'Transaction Count', 'Total Amount'])
    
    for month in range(1, 13):
        month_transactions = transactions.filter(date__month=month)
        count = month_transactions.count()
        amount = month_transactions.aggregate(total=Sum('amount'))['total'] or 0
        writer.writerow([calendar.month_name[month], count, f'${amount:.2f}'])
    
    writer.writerow([])  # Empty row for spacing
    
    # Category breakdown
    writer.writerow(['CATEGORY BREAKDOWN'])
    writer.writerow(['Category', 'Transaction Count', 'Total Amount'])
    
    category_breakdown = transactions.values('category') \
        .annotate(total=Sum('amount'), count=Count('id')) \
        .order_by('-total')
    
    for category in category_breakdown:
        writer.writerow([
            category['category'].title(), 
            category['count'], 
            f'${category["total"]:.2f}'
        ])
    
    writer.writerow([])  # Empty row for spacing
    
    # Savings goals
    if goals.exists():
        writer.writerow(['SAVINGS GOALS'])
        writer.writerow(['Goal Name', 'Current Amount', 'Target Amount', 'Progress (%)'])
        
        for goal in goals:
            writer.writerow([
                goal.name,
                f'${goal.current_amount:.2f}',
                f'${goal.target_amount:.2f}',
                f'{goal.progress_percentage():.0f}%'
            ])
        
        writer.writerow([])  # Empty row for spacing
    
    # Monthly budgets
    current_budgets = MonthlyBudget.objects.filter(
        user=request.user,
        month__year=year
    ).order_by('month')
    
    if current_budgets.exists():
        writer.writerow(['MONTHLY BUDGETS'])
        writer.writerow(['Month', 'Category', 'Budget Amount'])
        
        for budget in current_budgets:
            writer.writerow([
                budget.month.strftime('%B %Y'),
                budget.category.get_name_display(),
                f'${budget.amount:.2f}'
            ])
    
    return response
