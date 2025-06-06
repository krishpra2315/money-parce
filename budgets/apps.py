from django.apps import AppConfig

class BudgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budgets'

    def ready(self):
        import budgets.signals # Import to connect receivers 