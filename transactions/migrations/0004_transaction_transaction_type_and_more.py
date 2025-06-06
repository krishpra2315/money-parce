# Generated by Django 5.2 on 2025-04-23 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_transaction_pending_transaction_plaid_account_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('expense', 'Expense'), ('income', 'Income')], default='expense', max_length=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='Always positive value', max_digits=10),
        ),
    ]
