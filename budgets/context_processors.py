from .models import MonthlyBudget

def budget_alerts(request):
    if request.user.is_authenticated:
        alerts = MonthlyBudget.get_current_alerts(request.user)
        return {'budget_alerts': alerts}
    return {'budget_alerts': []} 