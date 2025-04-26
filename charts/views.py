from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
from transactions.models import Transaction
from transactions.forms import TransactionFilterForm
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to avoid requiring a display
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from io import BytesIO
import base64
import numpy as np
import datetime
import calendar

@login_required
def charts_dashboard(request):
    """Main dashboard for transaction charts and spending analysis"""
    # Default to current year
    year = datetime.datetime.now().year
    month = None
    
    # Generate charts
    category_chart = generate_category_pie_chart(request.user, year, month)
    monthly_spending_chart = generate_monthly_spending_chart(request.user, year)
    
    context = {
        'category_chart': category_chart,
        'monthly_spending_chart': monthly_spending_chart,
        'selected_year': year,
        'selected_month': month,
        'current_year': datetime.datetime.now().year,
    }
    
    return render(request, 'charts/dashboard.html', context)

def generate_category_pie_chart(user, year=None, month=None):
    """Generate a pie chart of spending by category"""
    # Create base queryset for user's transactions, excluding income
    transactions = Transaction.objects.filter(
        user=user,
        transaction_type='expense' # Exclude income transactions
    )
    
    # Apply year and month filters
    if year:
        transactions = transactions.filter(date__year=year)
    if month:
        transactions = transactions.filter(date__month=month)
    
    # Get spending by category
    category_spending = transactions.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # If no data, return None
    if not category_spending:
        return None
    
    # Get categories and amounts
    categories = [category['category'] for category in category_spending]
    amounts = [float(category['total']) for category in category_spending]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Use a colorful color map
    colors = plt.cm.tab10.colors[:len(categories)]
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        amounts, 
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 12}
    )
    
    # Equal aspect ratio ensures the pie chart is circular
    ax.axis('equal')
    
    # Add a legend with spending amounts
    legend_labels = [f"{cat.title()} (${amt:.2f})" for cat, amt in zip(categories, amounts)]
    ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5))
    
    # Add title
    if month:
        month_name = calendar.month_name[month]
        title = f"Spending by Category - {month_name} {year}"
    else:
        title = f"Spending by Category - {year}"
    
    plt.title(title, fontsize=16)
    plt.tight_layout()
    
    # Save figure to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    
    # Encode the image to base64 string
    buf.seek(0)
    chart_img = base64.b64encode(buf.read()).decode('utf-8')
    
    return chart_img

def generate_monthly_spending_chart(user, year=None):
    """Generate a bar chart of spending by month for a given year"""
    # Default to current year if not specified
    if not year:
        year = datetime.datetime.now().year
    
    # Get all expense transactions for the user in the given year
    transactions = Transaction.objects.filter(
        user=user,
        date__year=year,
        transaction_type='expense' # Exclude income transactions
    )
    
    # Get spending by month
    monthly_spending = transactions.annotate(
        month=ExtractMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Initialize data for all months (1-12)
    all_months = {m: 0 for m in range(1, 13)}
    
    # Fill in the actual data
    for item in monthly_spending:
        all_months[item['month']] = float(item['total'])
    
    # Get month names and amounts
    month_names = [calendar.month_abbr[m] for m in range(1, 13)]
    amounts = list(all_months.values())
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar chart
    bars = ax.bar(
        month_names, 
        amounts, 
        color=plt.cm.Blues(np.linspace(0.4, 0.8, 12))
    )
    
    # Add data labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2., 
                height + 5,
                f'${height:.0f}', 
                ha='center', 
                va='bottom', 
                fontsize=10
            )
    
    # Add labels and title
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Total Spending ($)', fontsize=12)
    ax.set_title(f'Monthly Spending for {year}', fontsize=16)
    ax.tick_params(axis='x', rotation=0)
    
    # Add grid lines for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save figure to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    
    # Encode the image to base64 string
    buf.seek(0)
    chart_img = base64.b64encode(buf.read()).decode('utf-8')
    
    return chart_img
