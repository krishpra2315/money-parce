from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from .models import Scholarship, CollegeDebt
from .forms import ScholarshipForm, CollegeDebtForm
from decimal import Decimal

def is_eligible_for_scholarships(user):
    """Check if the user is eligible for scholarships (age between 18-22)"""
    return user.age is not None and 18 <= user.age <= 22

@login_required
def scholarship_dashboard(request):
    """Main scholarship dashboard, only accessible to eligible users."""
    if not is_eligible_for_scholarships(request.user):
        messages.error(request, "You must be between 18-22 years old to access scholarships.")
        return redirect('home')
    
    # Get user's scholarships
    scholarships = Scholarship.objects.filter(user=request.user).order_by('-date_added')
    
    # Get or initialize college debt
    college_debt, created = CollegeDebt.objects.get_or_create(
        user=request.user,
        defaults={'total_amount': Decimal('0.00')}
    )
    
    # Calculate totals and coverage
    total_scholarships = scholarships.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    coverage_percentage = college_debt.scholarship_coverage_percentage()
    
    # Forms for adding new data
    scholarship_form = ScholarshipForm()
    debt_form = CollegeDebtForm(instance=college_debt)
    
    if request.method == 'POST':
        if 'add_scholarship' in request.POST:
            scholarship_form = ScholarshipForm(request.POST)
            if scholarship_form.is_valid():
                scholarship = scholarship_form.save(commit=False)
                scholarship.user = request.user
                scholarship.save()
                messages.success(request, "Scholarship added successfully!")
                return redirect('scholarships:dashboard')
                
        elif 'update_debt' in request.POST:
            debt_form = CollegeDebtForm(request.POST, instance=college_debt)
            if debt_form.is_valid():
                debt_form.save()
                messages.success(request, "College debt updated successfully!")
                return redirect('scholarships:dashboard')
    
    context = {
        'scholarships': scholarships,
        'college_debt': college_debt,
        'total_scholarships': total_scholarships,
        'coverage_percentage': coverage_percentage,
        'scholarship_form': scholarship_form,
        'debt_form': debt_form,
    }
    
    return render(request, 'scholarships/dashboard.html', context)

@login_required
def delete_scholarship(request, scholarship_id):
    """Delete a scholarship."""
    if not is_eligible_for_scholarships(request.user):
        messages.error(request, "You must be between 18-22 years old to access scholarships.")
        return redirect('home')
        
    scholarship = get_object_or_404(Scholarship, id=scholarship_id, user=request.user)
    
    if request.method == 'POST':
        scholarship.delete()
        messages.success(request, "Scholarship deleted successfully!")
        return redirect('scholarships:dashboard')
    
    return render(request, 'scholarships/confirm_delete.html', {'scholarship': scholarship})

@login_required
def scholarship_data(request):
    """API endpoint to get scholarship data for Ajax updates."""
    if not is_eligible_for_scholarships(request.user):
        return JsonResponse({'error': 'Not eligible'}, status=403)
        
    scholarships = Scholarship.objects.filter(user=request.user)
    try:
        college_debt = CollegeDebt.objects.get(user=request.user)
    except CollegeDebt.DoesNotExist:
        college_debt = CollegeDebt.objects.create(user=request.user, total_amount=Decimal('0.00'))
    
    total_scholarships = scholarships.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    coverage_percentage = college_debt.scholarship_coverage_percentage()
    
    return JsonResponse({
        'total_scholarships': float(total_scholarships),
        'total_debt': float(college_debt.total_amount),
        'coverage_percentage': float(coverage_percentage)
    })
