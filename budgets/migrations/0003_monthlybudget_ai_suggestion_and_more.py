# Generated by Django 5.2 on 2025-04-19 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0002_alter_budgetcategory_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlybudget',
            name='ai_suggestion',
            field=models.TextField(blank=True, help_text='AI-generated suggestion for saving money in this category.', null=True),
        ),
        migrations.AddField(
            model_name='monthlybudget',
            name='suggestion_generated',
            field=models.BooleanField(default=False, help_text='Indicates if an AI suggestion has been generated since crossing the threshold.'),
        ),
    ]
